import os
import logging
import numpy as np
import pandas as pd

from PIL import Image
from pathlib import Path
from vedo import Axes, Mesh, Plotter, Sphere, settings
from typing import Dict, Literal, Optional, Union, Tuple

from .head_cleaner import HeadCleaner
from .cap_extractor import CapExtractor
from .head_capturer import HeadCapturer
from .head_pose_aligner import HeadPoseAligner
from .electrode_curvature_detector import ElectrodeCurvatureDetector


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class MeshLoader:
    def __init__(
        self,
        mesh_path: Union[str, Path],
        texture_path: Optional[Union[str, Path]] = None,
        fiducials_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Initialize the 3D head scanned mesh loader.
        """
        self.mesh = self._load_mesh(mesh_path)
        self.mesh_raw = self.mesh.clone() if self.mesh is not None else None
        self.mesh_preprocessed = self.mesh.clone() if self.mesh is not None else None
        self.mesh_cleaned = self.mesh.clone() if self.mesh is not None else None
        self.mesh_extracted = self.mesh.clone() if self.mesh is not None else None
        self.texture = self._load_texture(texture_path) if texture_path is not None else None
        self.fiducials = self._load_fiducials(fiducials_path)
        self.preprocessed = False
        self.curvatures = None

        self.aligner = None
        self.capturer = None
        self.cleaner = None
        self.cap_extractor = None
        self.curvature_extractor = None

        self.preprocess_data()

    def _load_mesh(self, mesh_path: Union[str, Path]) -> Mesh:
        """
        Load a 3D mesh from a file.
        """
        if not os.path.exists(mesh_path):
            logging.error(f"Mesh file not found: {mesh_path}")
            return None
        logging.info(f"Loading mesh from {mesh_path}")
        mesh = Mesh(mesh_path)
        return mesh

    def _load_texture(self, texture_path: Union[str, Path]) -> np.ndarray:
        """
        Load a texture/image for mesh mapping from a file.
        """
        if not os.path.exists(texture_path):
            logging.error(f"Texture file not found: {texture_path}")
            return None
        logging.info(f"Loading texture from {texture_path}")
        image = Image.open(texture_path)
        texture = np.array(image)
        self._apply_texture(texture)
        return texture

    def _load_fiducials(self, fiducials_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load fiducial points from a CSV file.
        - Fiducial codes are indices.
        """
        if fiducials_path is None:
            logging.warning("Fiducials file not provided")
            return None
        if not os.path.exists(fiducials_path):
            logging.error(f"Fiducials file not found: {fiducials_path}")
            return None

        fiducials = pd.read_csv(fiducials_path, header=None, index_col=0)
        return fiducials

    def _apply_texture(self, texture: np.ndarray) -> None:
        """
        Apply the loaded texture to the mesh.
        """
        if self.mesh is not None and texture is not None:
            logging.info("Applying texture to the mesh...")
            self.mesh.texture(texture)

    def _compute_scale_factor(self) -> float:
        """
        Estimate the scale factor needed to convert the mesh into millimeter units.
        """
        if self.fiducials is not None:
            fiducial_pairs = [
                ("NAS", "INI"),
                ("LPA", "RPA"),
                ("NAS", "LPA"),
                ("NAS", "RPA"),
            ]

            # Compute all available fiducial distances
            distances = [
                np.linalg.norm(self.fiducials.loc[p1] - self.fiducials.loc[p2])
                for p1, p2 in fiducial_pairs
                if p1 in self.fiducials.index and p2 in self.fiducials.index
            ]
            distance = max(distances) if distances else None

        # Use mesh bounds
        bounds = self.mesh.bounds()
        width = bounds[1] - bounds[0]
        height = bounds[3] - bounds[2]
        depth = bounds[5] - bounds[4]
        distance = max(width, height, depth)

        # Detect units based on typical head dimensions
        if distance < 1:  # meters -> millimeters
            return 1000.0
        elif distance < 100:  # centimeters -> millimeters
            return 10.0
        else:  # already millimeters
            return 1.0

    def _convert_to_mm(self) -> None:
        """
        Convert the mesh to millimeter scale.
        """
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")

        scale_factor = self._compute_scale_factor()
        logging.info(f"Scale factor for conversion: {scale_factor}")

        if scale_factor != 1.0:
            self.mesh.scale(scale_factor)

    def preprocess_data(self) -> None:
        """
        Preprocess the loaded mesh data.
        """
        if self.preprocessed:
            logging.info("Mesh data already preprocessed")
            return
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")
        logging.info("Preprocessing data...")

        # Remove duplicate vertices (if any)
        if self.mesh.npoints != len(set(map(tuple, self.mesh.points()))):
            logging.info("Removing duplicate vertices from the mesh...")
            self.mesh.clean()

        # Convert to mm scale first
        self._convert_to_mm()

        # Center using center of mass (alternative: bounding box center)
        center_of_mass = self.mesh.center_of_mass()
        self.mesh.pos(-center_of_mass)

        # Orient into the standard coordinate center
        if self.fiducials is not None:
            logging.info("Orienting head mesh and fiducials...")
            self.aligner = HeadPoseAligner(self.mesh, self.fiducials, self.texture)
            self.mesh, self.fiducials = self.aligner.orient_head_mesh()

        # Fill small holes
        self.mesh.fill_holes(size=10.0)

        # Smooth
        self.mesh.smooth(niter=10, pass_band=0.25, edge_angle=10, feature_angle=30)

        # Decimate
        # self.mesh.decimate(0.9)

        # Compute normals (better visualization)
        self.mesh.compute_normals()

        self.preprocessed = True
        self.mesh_preprocessed = self.mesh.clone()

    def clean_data(
        self,
        x_margin: Optional[float] = 0.5,
        y_top_margin: Optional[float] = 0.25,
        y_bottom_margin: Optional[float] = 1.0,
        z_margin: Optional[float] = 0.25,
    ) -> None:
        """
        Clean the loaded mesh data.
        """
        if not self.preprocessed:
            raise ValueError("Data must be preprocessed before cleaning")
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")
        if self.fiducials is None:
            raise ValueError("Fiducials are not loaded")
        logging.info("Cleaning data...")

        # Crop to bounding box with margins and remove unwanted objects
        self.cleaner = HeadCleaner(self.mesh, self.fiducials, self.texture)
        self.cleaner.crop_with_bounding_box(
            x_margin=x_margin,
            y_top_margin=y_top_margin,
            y_bottom_margin=y_bottom_margin,
            z_margin=z_margin,
        )
        self.cleaner.clean_from_unwanted_objects()

        self.mesh_cleaned = self.cleaner.get_cleaned_mesh()
        self.mesh = self.mesh_cleaned.clone()

    def extract_cap_data(self, margin: float = 0.0) -> None:
        """
        Extract the cap portion of the mesh (above the fiducial plane).
        """
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")
        if self.fiducials is None:
            raise ValueError("Fiducials are not loaded")

        logging.info("Extracting cap data (margin=%.2f)...", margin)

        # Initialize extractor
        self.cap_extractor = CapExtractor(self.mesh, self.fiducials, self.texture)

        # Perform cap extraction
        self.cap_extractor.extract_cap(margin=margin)

        # Store cap results
        self.mesh_extracted = self.cap_extractor.mesh.clone()
        self.mesh = self.mesh_extracted.clone()

        # Initialize curvature detector/extractor
        self.curvature_extractor = ElectrodeCurvatureDetector(self.mesh)

        # Compute maps
        # self.curvatures = self.curvature_extractor.extract_curvatures()

    def capture_data(
        self,
        output_dir: Union[str, Path],
        image_size: Tuple[int, int] = (1024, 1024),
        show_fiducials: bool = True,
        show_bounding_box: bool = True,
        show_coordinate_vectors: bool = True,
        show_cap_plane: bool = True,
        custom_cmap: Literal["saliency", "probability", "gradient"] = None,
        show_axes: bool = True,
    ) -> None:
        """
        Capture mesh data from multiple views and save screenshots.
        """
        if self.mesh is None:
            raise ValueError("Mesh is not loaded.")
        if self.fiducials is None:
            raise ValueError("Fiducials are not loaded.")
        mesh = self.mesh.clone()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logging.info("Capturing mesh data to %s...", output_dir)

        # Default settings
        mesh_alpha = 1.0
        center = np.mean(
            [self.fiducials.loc[label].values for label in ["NAS", "INI", "LPA", "RPA"]],
            axis=0,
        )

        # If an aligner exists, update center and transparency
        if self.aligner is not None:
            mesh_alpha = 0.25
            center = self.aligner.origin

        # Custom colormap
        cmap = None
        if custom_cmap is not None:
            cmap_map = {
                "saliency": "saliency_map",
                "probability": "probability_map",
                "gradient": "gradient_directions",
            }

            key = cmap_map.get(custom_cmap)
            if key is not None:
                cmap = self.curvatures[key]
                if key == "gradient":
                    cmap = np.linalg.norm(cmap, axis=1)

        # Initialize capturer
        self.capturer = HeadCapturer(mesh, self.fiducials, center, self.texture)

        # Capture multi-view images
        self.capturer.capture_all_views(
            output_dir=output_dir,
            image_size=image_size,
            show_cap=show_cap_plane and self.cap_extractor is not None,
            cmap=cmap if cmap is not None and custom_cmap is not None else None,
        )

        # Prepare optional overlays
        fiducials = self.fiducials if show_fiducials else None
        bounding_box = getattr(self.cleaner, "bounding_box", None) if show_bounding_box else None
        coordinate_vectors = (
            getattr(self.aligner, "coordinate_vectors", None) if show_coordinate_vectors else None
        )
        cap_plane = getattr(self.cap_extractor, "plane", None) if show_cap_plane else None

        # Don't show bounding box when displaying cap plane
        if show_cap_plane and self.cap_extractor is not None:
            bounding_box = None

        # Curvature candidates
        curvatures = None
        if custom_cmap is not None and self.curvatures is not None:
            curvatures = [candidate["position"] for candidate in self.curvatures["candidates"]]

        # Capture a custom single view with overlays
        self.capturer.capture_single_view(
            mesh=mesh,
            name="custom",
            output_dir=output_dir,
            center=center,
            image_size=image_size,
            mesh_alpha=mesh_alpha,
            mesh_color=None,
            fiducials=fiducials,
            bounding_box=bounding_box,
            coordinate_vectors=coordinate_vectors,
            cap_plane=cap_plane,
            cmap=cmap if cmap is not None and custom_cmap is not None else None,
            curvatures=curvatures,
            show_axes=show_axes,
        )

    def get_plotter(
        self,
        show_axes: bool = False,
        show_fiducials: bool = False,
        mesh_alpha: float = 1.0,
    ) -> Plotter:
        """
        Visualize the loaded mesh data.
        """
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")

        plotter = Plotter(title="Electrode Localization Kit", size=(1200, 800))

        # Mesh appearance
        self.mesh.alpha(mesh_alpha)
        if self.texture is None:
            self.mesh.color("black").alpha(0.25)
        plotter.add(self.mesh)

        # Fiducials
        if show_fiducials and self.fiducials is not None:
            fiducial_spheres = [
                Sphere(pos=fiducial, r=2.5, c="red") for fiducial in self.fiducials.values
            ]
            plotter.add(fiducial_spheres)

        # Global axes
        if show_axes:
            axes_actor = Axes(self.mesh, xtitle="X", ytitle="Y", ztitle="Z")
            plotter.add(axes_actor)

        return plotter

    def get_summary(self) -> Dict[str, Union[int, float]]:
        """
        Get a summary of the mesh properties.
        """
        summary = {
            "mesh_loaded": self.mesh is not None,
            "texture_loaded": self.texture is not None,
            "fiducials_loaded": self.fiducials is not None,
            "preprocessed": self.preprocessed,
        }

        if self.mesh is not None:
            summary.update(
                {
                    "num_vertices": self.mesh.npoints,
                    "num_faces": self.mesh.ncells,
                    "bounds": self.mesh.bounds().tolist(),
                    "center_of_mass": self.mesh.center_of_mass().tolist(),
                }
            )

        if self.fiducials is not None:
            summary.update(
                {
                    "fiducials": self.fiducials.index.tolist(),
                    "num_fiducials": len(self.fiducials),
                }
            )

        return summary
