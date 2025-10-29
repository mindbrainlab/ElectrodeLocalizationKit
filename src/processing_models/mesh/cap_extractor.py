import logging
import numpy as np
import pandas as pd

from typing import List, Optional, Tuple
from vedo import Mesh, Plane, Plotter, Sphere, settings

from .head_cleaner import HeadCleaner


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CapExtractor:
    def __init__(
        self,
        mesh: Mesh,
        fiducials: pd.DataFrame,
        texture: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize the cap extractor to isolate the cap portion of a head mesh above the plane.
        """
        self.mesh_raw = mesh.clone()
        self.mesh = mesh.clone()
        self.mesh_cap = None
        self.texture = texture.copy() if texture is not None else None
        self.fiducials = fiducials.copy()
        self.plane = None

        if texture is None:
            self.mesh.texture(None).color("gray")

    def _get_fiducials(self, labels: List[str]) -> List[np.ndarray]:
        """
        Extract and validate fiducial points.
        """
        missing = [lbl for lbl in labels if lbl not in self.fiducials.index]
        if missing:
            raise ValueError(f"Missing fiducials: {', '.join(missing)}")

        return [self.fiducials.loc[label].to_numpy(dtype=float).copy() for label in labels]

    def _compute_cutting_plane(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the cutting plane defined by NAS-LPA-RPA fiducials.
        """
        nas, lpa, rpa = self._get_fiducials(["NAS", "LPA", "RPA"])
        points = np.array([nas, lpa, rpa])

        center = points.mean(axis=0)

        # Plane normal via SVD (robust to collinearity)
        _, _, vh = np.linalg.svd(points - center)
        normal = vh[-1] / np.linalg.norm(vh[-1])

        # Flip normal to point upward
        if normal[1] < 0:
            normal = -normal

        logging.info(f"Cutting plane: center={center}, normal={normal}")
        return center, normal

    def extract_cap(self, margin: float = 0.0) -> Mesh:
        """
        Extract the cap portion of the mesh above the cutting plane.
        """
        center, normal = self._compute_cutting_plane()
        self.plane = {"center": center, "normal": normal}

        adjusted_center = center - margin * normal

        # Cut everything above plane
        self.mesh = self.mesh.cut_with_plane(origin=adjusted_center, normal=normal)

        # Keep largest connected component only
        self.cleaner = HeadCleaner(self.mesh, self.fiducials, self.texture)
        self.cleaner.clean_from_unwanted_objects()

        self.mesh_cap = self.mesh.clone()
        return self.mesh_cap

    def _add_plane_visualization(self, plotter: Plotter) -> None:
        """
        Add a plane visualization to the plotter.
        """
        bounds = self.mesh.bounds()
        x_size_temp, z_size_temp = bounds[1] - bounds[0], bounds[5] - bounds[4]
        center, normal = self.plane["center"], self.plane["normal"]

        # Adjust plane size using fiducials if available
        if {"NAS", "INI", "LPA", "RPA"}.issubset(self.fiducials.index):
            nas, ini, lpa, rpa = self._get_fiducials(["NAS", "INI", "LPA", "RPA"])
            x_size_temp = abs(lpa[0] - rpa[0])
            z_size_temp = abs(nas[2] - ini[2])
            center = np.mean([nas, lpa, rpa], axis=0)

        # Make plane roughly square
        x_size = x_size_temp * 0.75 + z_size_temp
        z_size = z_size_temp * 0.75 + x_size_temp

        plane = Plane(pos=center, normal=normal, s=(z_size, x_size), alpha=0.3).c("red")
        plotter.add(plane)

    def visualize_extraction(
        self,
        show_fiducials: bool = True,
        show_plane: bool = True,
    ) -> None:
        """
        Visualize the extraction process.
        """
        plotter = Plotter(title="EEG Head Mesh Processing Result")
        plotter.add(self.mesh)

        if show_fiducials:
            fiducial_spheres = [
                Sphere(pos=coords, r=2.5, c="red") for coords in self.fiducials.values
            ]
            plotter.add(fiducial_spheres)

        if show_plane and self.plane is not None:
            self._add_plane_visualization(plotter)

        plotter.show()
