import logging
import numpy as np
import pandas as pd

from collections import defaultdict
from vedo import Mesh, Plotter, Spheres
from typing import Dict, List, Tuple, Any, Optional

from .view_type import ViewType
from .detection_method import DetectionMethod
from .electrode_merger import ElectrodeMerger


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ElectrodeMapper:

    def __init__(
        self,
        mesh: Mesh,
        mesh_cap: Mesh,
        fiducials: pd.DataFrame,
        center: Optional[np.ndarray] = None,
    ):
        """
        Initialize mapper that maps 2D detected eletrodes back to 3D mesh coordinates using ray casting.
        """
        self.mesh = mesh.clone()
        self.mesh_cap = mesh_cap.clone()
        self.fiducials = fiducials.copy()
        self.electrodes = None

        # Default center if none provided
        self.center = center.copy() if center is not None else np.array([0, 0, 0])

        # Setup standard orthogonal camera views
        self._setup_cameras()

    @staticmethod
    def _setup_camera(center: np.ndarray, camera_distance: Dict[str, float]) -> Dict[str, Any]:
        """
        Configure standard orthogonal camera views: front, back, right, left, top, bottom.
        """
        dx, dy, dz = (
            camera_distance["x"],
            camera_distance["y"],
            camera_distance["z"],
        )
        cx, cy, cz = center

        return {
            "center": center,
            "distance": camera_distance,
            "views": {
                "front": {
                    "pos": [cx, cy, cz + dz],
                    "up": [0, 1, 0],
                    "name": "front",
                    "description": "Front view (+Z)",
                },
                "back": {
                    "pos": [cx, cy, cz - dz],
                    "up": [0, 1, 0],
                    "name": "back",
                    "description": "Back view (-Z)",
                },
                "top": {
                    "pos": [cx, cy + dy, cz],
                    "up": [0, 0, -1],
                    "name": "top",
                    "description": "Top view (+Y)",
                },
                "bottom": {
                    "pos": [cx, cy - dy, cz],
                    "up": [0, 0, 1],
                    "name": "bottom",
                    "description": "Bottom view (-Y)",
                },
                "right": {
                    "pos": [cx - dx, cy, cz],
                    "up": [0, 1, 0],
                    "name": "right",
                    "description": "Right view (+X)",
                },
                "left": {
                    "pos": [cx + dx, cy, cz],
                    "up": [0, 1, 0],
                    "name": "left",
                    "description": "Left view (-X)",
                },
                "front_top": {
                    "pos": [cx, (cy + dy) * 0.75, (cz + dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "front_top",
                    "description": "Front-top view (+Z, +Y)",
                },
                "front_bottom": {
                    "pos": [cx, (cy - dy) * 0.75, (cz + dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "front_bottom",
                    "description": "Front-bottom view (+Z, -Y)",
                },
                "back_top": {
                    "pos": [cx, (cy + dy) * 0.75, (cz - dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "back_top",
                    "description": "Back-top view (-Z, +Y)",
                },
                "back_bottom": {
                    "pos": [cx, (cy - dy) * 0.75, (cz - dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "back_bottom",
                    "description": "Back-bottom view (-Z, -Y)",
                },
                "front_right": {
                    "pos": [(cx - dx) * 0.75, cy, (cz + dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "front_right",
                    "description": "Front-right view (+X, +Z)",
                },
                "front_left": {
                    "pos": [(cx + dx) * 0.75, cy, (cz + dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "front_left",
                    "description": "Front-left view (-X, +Z)",
                },
                "back_right": {
                    "pos": [(cx - dx) * 0.75, cy, (cz - dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "back_right",
                    "description": "Back-right view (+X, -Z)",
                },
                "back_left": {
                    "pos": [(cx + dx) * 0.75, cy, (cz - dz) * 0.75],
                    "up": [0, 1, 0],
                    "name": "back_left",
                    "description": "Back-left view (-X, -Z)",
                },
                "top_right": {
                    "pos": [(cx - dx) * 0.75, (cy + dy) * 0.75, cz],
                    "up": [0, 1, 0],
                    "name": "top_right",
                    "description": "Top-right view (+X, +Y)",
                },
                "top_left": {
                    "pos": [(cx + dx) * 0.75, (cy + dy) * 0.75, cz],
                    "up": [0, 1, 0],
                    "name": "top_left",
                    "description": "Top-left view (-X, +Y)",
                },
                "bottom_right": {
                    "pos": [(cx - dx) * 0.75, (cy - dy) * 0.75, cz],
                    "up": [0, 1, 0],
                    "name": "top_right",
                    "description": "Bottom-right view (+X, -Y)",
                },
                "bottom_left": {
                    "pos": [(cx + dx) * 0.75, (cy - dy) * 0.75, cz],
                    "up": [0, 1, 0],
                    "name": "top_left",
                    "description": "Bottom-left view (-X, -Y)",
                },
            },
        }

    def _setup_cameras(self) -> None:
        """
        Setup camera configurations for the mesh.
        """
        # Estimate a reasonable camera distance from mesh bounds
        center = self.center.copy()
        bounds = self.mesh_cap.bounds()
        camera_distance = {
            "x": (bounds[1] - bounds[0]) * 2.5,
            "y": (bounds[3] - bounds[2]) * 1.75,
            "z": (bounds[5] - bounds[4]) * 2.5,
        }

        # Define a custom camera position based on fiducials (for cap views)
        if self.fiducials is not None:
            required_labels = ["NAS", "LPA", "RPA"]

            if set(required_labels).issubset(self.fiducials.index):
                # Extract fiducial coordinates
                fiducials = {
                    label: self.fiducials.loc[label].to_numpy(dtype=float)
                    for label in required_labels
                }

                nas, lpa, rpa = fiducials["NAS"], fiducials["LPA"], fiducials["RPA"]
                plane_center = np.mean([nas, lpa, rpa], axis=0)

                # Update center.y to position the camera above the cropped mesh
                center_y = (bounds[3] - plane_center[2]) / 2.0
                center[1] = center_y

                # Set camera distance in y direction (scaled by bounding box extent)
                bbox_y_extent = bounds[3] - bounds[2]
                camera_distance["y"] = bbox_y_extent * 2.75

        # Setup camera positions
        self.camera_config = self._setup_camera(center, camera_distance)

    def _pixel_to_ray(
        self,
        pixel_coords: Tuple[int, int],
        view_type: ViewType,
        image_size: Tuple[int, int],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert 2D pixel coordinates to 3D world ray (origin and direction).
        """
        if self.camera_config is None:
            raise ValueError("Camera configuration not set")

        # Calculate camera coordinate system
        camera_pos = np.array(self.camera_config["views"][view_type.label]["pos"])
        focal_point = np.array(self.camera_config["center"])
        view_up = np.array(self.camera_config["views"][view_type.label]["up"])

        # Convert pixel coordinates to normalized device coordinates (-1 to 1)
        width, height = image_size[:2]
        x_pixel, y_pixel = pixel_coords
        x_ndc = (2.0 * x_pixel / width) - 1.0
        y_ndc = 1.0 - (2.0 * y_pixel / height)  # Flip Y axis

        # Forward vector (from camera to focal point)
        forward = focal_point - camera_pos
        forward = forward / np.linalg.norm(forward)

        # Right vector
        right = np.cross(forward, view_up)
        right = right / np.linalg.norm(right)

        # Corrected up vector
        up = np.cross(right, forward)
        up = up / np.linalg.norm(up)

        # Calculate ray direction
        aspect_ratio = width / height
        fov_rad = np.radians(30.0)  # Default view angle

        # Calculate the ray direction in camera space
        tan_half_fov = np.tan(fov_rad / 2.0)
        ray_x = x_ndc * tan_half_fov * aspect_ratio
        ray_y = y_ndc * tan_half_fov

        # Transform to world coordinates
        ray_origin = camera_pos
        ray_direction = forward + ray_x * right + ray_y * up
        ray_direction = ray_direction / np.linalg.norm(ray_direction)

        return ray_origin, ray_direction

    def _ray_mesh_intersection(
        self, ray_origin: np.ndarray, ray_direction: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Find intersection point between ray and mesh surface.
        """
        # Perform ray-mesh intersection using Vedo
        t = 1000  # Extend ray far enough
        ray_end = ray_origin + ray_direction * t

        # Use Vedo's intersectWithLine method
        intersection_points = self.mesh_cap.intersect_with_line(ray_origin, ray_end)

        if len(intersection_points) > 0:
            # Find closest intersection point to camera
            points_array = np.array([p for p in intersection_points])
            distances = np.linalg.norm(points_array - ray_origin, axis=1)
            closest_idx = np.argmin(distances)
            return points_array[closest_idx]

        return None

    def _flatten_electrode_map(
        self,
        mapped_electrodes: Dict[
            ViewType, Dict[DetectionMethod, List[Tuple[float, float, float, str]]]
        ],
    ) -> List[Tuple[ViewType, DetectionMethod, float, float, float, str]]:
        """
        Flatten a nested dictionary of 3D electrode coordinates into a list of tuples.
        """
        flatten_electrodes = []
        for view, method_dict in mapped_electrodes.items():
            for method, coords_list in method_dict.items():
                for x, y, z, label in coords_list:
                    flatten_electrodes.append((view, method, x, y, z, label))
        return np.array(flatten_electrodes)

    def map_electrodes_to_3d(
        self,
        detected_electrodes: Dict[ViewType, Dict[DetectionMethod, List[Tuple[int, int, int, str]]]],
        metadata: Dict[ViewType, Dict[str, Any]],
    ) -> List[Tuple[ViewType, DetectionMethod, float, float, float, str]]:
        """
        Map detected 2D electrodes to 3D mesh coordinates.
        """
        mapped_electrodes = defaultdict(dict)

        for view_type, methods in detected_electrodes.items():
            if view_type.label not in self.camera_config["views"]:
                logging.warning(f"Unknown view {view_type}")
                continue
            logging.info(f"Mapping electrodes from {view_type} view")

            # Get image size from metadata
            shape = metadata.get(view_type, {}).get("shape")
            image_size = (1024, 1024)
            if shape is not None and len(shape) >= 2:
                image_size = tuple(shape[:2])

            for method, electrodes in methods.items():

                view_3d_coords = []
                for x, y, _, label in electrodes:
                    # Convert pixel to world ray
                    ray_origin, ray_direction = self._pixel_to_ray((x, y), view_type, image_size)

                    # Find intersection with mesh
                    intersection = self._ray_mesh_intersection(ray_origin, ray_direction)

                    if intersection is not None:
                        intersection = np.append(np.array(intersection, dtype=object), label)
                        view_3d_coords.append(intersection)
                    else:
                        logging.warning(
                            f"No intersection found for electrode {view_type}.{method} ({x}, {y})"
                        )

                mapped_electrodes[view_type][method] = view_3d_coords

        # Flatten map
        flatten_electrodes = self._flatten_electrode_map(mapped_electrodes)

        # Cluster electrodes
        merger = ElectrodeMerger(15.0)
        merged_electrodes = merger.cluster_electrodes(flatten_electrodes)
        self.electrodes = merged_electrodes.copy()

        return merged_electrodes

    def visualize_results(
        self,
        show_fiducials: bool = True,
    ) -> None:
        """
        Visualize the 3D mesh with mapped electrodes.
        """
        if self.electrodes is None:
            raise ValueError("Electrodes not merged")

        plotter = Plotter(title="EEG Electrode Mapping Results")
        plotter.add(self.mesh)

        # Add electrodes
        spheres = Spheres(self.electrodes[:, (2, 3, 4)], r=3.5, c="gray")
        plotter.add(spheres)

        # Add fiducial points
        if show_fiducials and self.fiducials is not None:
            fiducial_spheres = Spheres(self.fiducials, r=2.5, c="red")
            plotter.add(fiducial_spheres)

        plotter.show()

    def save(
        self,
        file_path: str,
        electrodes: Optional[
            List[Tuple[ViewType, DetectionMethod, float, float, float, str]]
        ] = None,
    ) -> None:
        """
        Save detected EEG electrodes to a CSV file.
        Format: ViewType,DetectionMethod,x,y,z
        """
        if electrodes is None:
            if self.electrodes is None:
                raise ValueError("Electrodes not merged")
            electrodes = self.electrodes

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for fid in electrodes:
                    if fid is not None:
                        f.write(
                            f"{fid[0].name},{fid[1].name},{fid[2]},{fid[3]},{fid[4]},{fid[5]}\n"
                        )
            logging.info(f"Electrodes saved to {file_path}")
        except OSError as e:
            logging.error(f"Failed to save electrodes: {e}")
