import logging
import numpy as np
import pandas as pd

from vtk import vtkPolyDataConnectivityFilter
from typing import Any, Dict, List, Optional, Union
from vedo import Box, Mesh, Plane, Plotter, Sphere, settings


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HeadCleaner:
    def __init__(
        self,
        mesh: Mesh,
        fiducials: pd.DataFrame,
        texture: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize the head cleaning processor.
        """
        self.mesh_raw = mesh.clone()
        self.fiducials = fiducials.copy()
        self.texture = texture.copy() if texture is not None else None

        self.mesh_cropped = None
        self.mesh_cleaned = None
        self.bounding_box = None

    def _get_fiducials(self, required_list) -> List[np.ndarray]:
        """
        Extract fiducials and validate they exist.
        """
        for fid in required_list:
            if fid not in self.fiducials.index:
                raise ValueError(f"Required fiducial {fid} not found")

        return [self.fiducials.loc[fid].to_numpy().astype(float).copy() for fid in required_list]

    def crop_with_bounding_box(
        self,
        x_margin: float = 0.5,
        y_top_margin: float = 0.25,
        y_bottom_margin: float = 1.0,
        z_margin: float = 0.25,
    ) -> Dict[str, Any]:
        """
        Create a bounding box based on fiducials with margins and crop the mesh.

        x: left-right -> symmetric margin (fraction of size)
        y: bottom-up -> top and bottom handled separately (larger bottom margin)
        z: back-forward -> symmetric margin
        """
        if self.mesh_raw is None:
            raise ValueError("Mesh is not loaded")

        # Get required fiducials
        required_fids = ["NAS", "LPA", "RPA", "INI", "VTX"]
        nas, lpa, rpa, ini, vtx = self._get_fiducials(required_fids)
        fiducials = np.stack([nas, lpa, rpa, ini, vtx], axis=0)

        # Compute min/max along each axis
        mins, maxs = fiducials.min(axis=0), fiducials.max(axis=0)
        x_min, y_min, z_min = mins
        x_max, y_max, z_max = maxs

        # Compute ranges
        x_range, y_range, z_range = maxs - mins

        # Apply margins
        x_min_final = x_min - x_margin * x_range
        x_max_final = x_max + x_margin * x_range
        y_min_final = y_min - y_bottom_margin * y_range
        y_max_final = y_max + y_top_margin * y_range
        z_min_final = z_min - z_margin * z_range
        z_max_final = z_max + z_margin * z_range

        # Store bounding box info
        self.bounding_box = {
            "bounds": [
                float(x_min_final),
                float(x_max_final),
                float(y_min_final),
                float(y_max_final),
                float(z_min_final),
                float(z_max_final),
            ],
            "center": np.array(
                [
                    (x_min_final + x_max_final) / 2,
                    (y_min_final + y_max_final) / 2,
                    (z_min_final + z_max_final) / 2,
                ]
            ),
            "size": (
                x_max_final - x_min_final,
                y_max_final - y_min_final,
                z_max_final - z_min_final,
            ),
        }

        # Get old bounds and position
        old_bounds = self.mesh_raw.bounds()
        pos = np.array(self.mesh_raw.center_of_mass())

        # Convert bounds to local coordinates
        x_min_local, x_max_local, y_min_local, y_max_local, z_min_local, z_max_local = old_bounds
        x_min_local, y_min_local, z_min_local = (
            np.array([x_min_local, y_min_local, z_min_local]) - pos
        )
        x_max_local, y_max_local, z_max_local = (
            np.array([x_max_local, y_max_local, z_max_local]) - pos
        )

        # New bounds (from bounding_box)
        x_min_final, x_max_final, y_min_final, y_max_final, z_min_final, z_max_final = (
            self.bounding_box["bounds"]
        )
        x_min_final, y_min_final, z_min_final = (
            np.array([x_min_final, y_min_final, z_min_final]) - pos
        )
        x_max_final, y_max_final, z_max_final = (
            np.array([x_max_final, y_max_final, z_max_final]) - pos
        )

        # Calculate dimensions
        dx = x_max_local - x_min_local
        dy = y_max_local - y_min_local
        dz = z_max_local - z_min_local

        # Calculate clipping proportions
        left = (x_min_final - x_min_local) / dx if dx != 0 else 0
        right = (x_max_local - x_max_final) / dx if dx != 0 else 0
        back = (y_min_final - y_min_local) / dy if dy != 0 else 0
        front = (y_max_local - y_max_final) / dy if dy != 0 else 0
        bottom = (z_min_final - z_min_local) / dz if dz != 0 else 0
        top = (z_max_local - z_max_final) / dz if dz != 0 else 0

        # Clamp to [0, 1] range
        left = max(0, min(1, left))
        right = max(0, min(1, right))
        back = max(0, min(1, back))
        front = max(0, min(1, front))
        bottom = max(0, min(1, bottom))
        top = max(0, min(1, top))

        # Crop the mesh
        self.mesh_cropped = self.mesh_raw.clone()
        self.mesh_cropped.crop(
            left=left,
            right=right,
            back=back,
            front=front,
            bottom=bottom,
            top=top,
        )
        if self.texture is not None:
            self.mesh_cropped.texture(self.texture)

        logging.info(f"Bounds before crop: {old_bounds}")
        logging.info(f"Bounds after crop: {self.bounding_box['bounds']}")
        logging.info(
            f"Cropped mesh: {self.mesh_raw.npoints} -> {self.mesh_cropped.npoints} ({(1 - self.mesh_cropped.npoints / self.mesh_raw.npoints) * 100:.1f}% reduction)"
        )

        return self.bounding_box

    def clean_from_unwanted_objects(self) -> Mesh:
        """
        Remove unwanted objects by keeping only the largest connected component.
        """
        if self.mesh_cropped is None:
            if self.mesh_raw is None:
                raise ValueError("Mesh is not loaded")
            logging.warning("No cropped mesh found, falling back to raw mesh")
            self.mesh_cropped = self.mesh_raw.clone()

        connectivity_filter = vtkPolyDataConnectivityFilter()
        connectivity_filter.SetInputData(self.mesh_cropped.polydata())
        connectivity_filter.SetExtractionModeToLargestRegion()
        connectivity_filter.Update()

        self.mesh_cleaned = Mesh(connectivity_filter.GetOutput())
        if self.texture is not None:
            self.mesh_cleaned.texture(self.texture)

        logging.info("Cleaned mesh: kept largest connected component")
        return self.mesh_cleaned

    def get_cleaned_mesh(self) -> Mesh:
        """
        Return the cleaned mesh.
        """
        if self.mesh_cleaned is not None:
            return self.mesh_cleaned
        logging.warning("No cleaned mesh available, returning cropped mesh")
        if self.mesh_cropped is not None:
            return self.mesh_cropped
        logging.error("No cropped mesh available, returning raw mesh")
        if self.mesh_raw is not None:
            return self.mesh_raw
        raise ValueError("No mesh data available for cleaning")

    def get_summary(self) -> Dict[str, Union[int, float, str]]:
        """
        Return summary of processing including mesh sizes, bounding box, and cleaning results.
        """
        summary = {
            "raw_points": self.mesh_raw.npoints if self.mesh_raw else None,
            "cropped_points": self.mesh_cropped.npoints if self.mesh_cropped else None,
            "cleaned_points": self.mesh_cleaned.npoints if self.mesh_cleaned else None,
            "bounding_box": self.bounding_box if self.bounding_box else None,
        }

        if self.mesh_raw and self.mesh_cropped:
            summary["crop_reduction_pct"] = 100 * (
                1 - self.mesh_cropped.npoints / self.mesh_raw.npoints
            )
        if self.mesh_cropped and self.mesh_cleaned:
            summary["clean_reduction_pct"] = 100 * (
                1 - self.mesh_cleaned.npoints / self.mesh_cropped.npoints
            )

        return summary

    def _create_box_planes(
        self, center: np.ndarray, x_size: float, y_size: float, z_size: float
    ) -> List[Plane]:
        """
        Create the 6 planes representing the bounding box faces.
        """
        # Apply small margin for visualization aesthetics
        margin = 0.025

        # Define the 6 faces of the box
        faces = [
            (
                "top",
                [0, 1, 0],
                [0, y_size / 2, 0],
                (z_size * (1 - margin), x_size * (1 - margin)),
            ),  # +Y face
            (
                "bottom",
                [0, -1, 0],
                [0, -y_size / 2, 0],
                (z_size * (1 - margin), x_size * (1 - margin)),
            ),  # -Y face
            (
                "right",
                [1, 0, 0],
                [x_size / 2, 0, 0],
                (z_size * (1 - margin), y_size * (1 - margin)),
            ),  # +X face
            (
                "left",
                [-1, 0, 0],
                [-x_size / 2, 0, 0],
                (z_size * (1 - margin), y_size * (1 - margin)),
            ),  # -X face
            (
                "front",
                [0, 0, 1],
                [0, 0, z_size / 2],
                (x_size * (1 - margin), y_size * (1 - margin)),
            ),  # +Z face
            (
                "back",
                [0, 0, -1],
                [0, 0, -z_size / 2],
                (x_size * (1 - margin), y_size * (1 - margin)),
            ),  # -Z face
        ]

        planes: List[Plane] = []
        for _, normal, offset, size in faces:
            plane_center = center + np.array(offset)
            plane = Plane(pos=plane_center, normal=normal, s=size)
            plane.alpha(0.25).color("gray")
            planes.append(plane)

        return planes

    def visualize_result(
        self,
        show_fiducials: bool = True,
        show_box_planes: bool = True,
        show_box_mesh: bool = False,
    ) -> None:
        """
        Visualize the processed mesh with fiducials and bounding box.
        """
        # Pick best available mesh (cleaned > cropped > raw)
        mesh = self.mesh_cleaned or self.mesh_cropped or self.mesh_raw
        if mesh is None:
            raise ValueError("No mesh available for visualization")

        plotter = Plotter(title="EEG Head Mesh Processing Result")
        plotter.add(mesh)

        # Add fiducial points
        if show_fiducials and self.fiducials is not None:
            fiducial_spheres = [
                Sphere(pos=fiducial, r=2.5, c="red") for fiducial in self.fiducials.values
            ]
            plotter.add(fiducial_spheres)

        # Add bounding box
        if self.bounding_box is None and (show_box_planes or show_box_mesh):
            logging.warning("Bounding box not defined, cannot display box visualization")
        elif show_box_planes:
            planes = self._create_box_planes(
                self.bounding_box["center"], *self.bounding_box["size"]
            )
            plotter.add(planes)
        elif show_box_mesh:
            box_mesh = (
                Box(pos=self.bounding_box["center"], size=self.bounding_box["size"])
                .alpha(0.25)
                .color("gray")
            )
            plotter.add(box_mesh)

        plotter.show()
