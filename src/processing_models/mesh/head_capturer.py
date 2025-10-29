import os
import logging
import numpy as np
import pandas as pd

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from vedo import Arrow, Axes, Mesh, Plane, Plotter, Sphere, Text3D, settings


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HeadCapturer:
    def __init__(
        self,
        mesh: Mesh,
        fiducials: pd.DataFrame,
        center: Optional[np.ndarray] = None,
        texture: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize to capture screenshots of a 3D head mesh from multiple camera views.
        """
        self.mesh = mesh.clone()
        self.fiducials = fiducials.copy()
        self.texture = texture.copy() if texture is not None else None

        # Apply mesh appearance
        self.mesh.alpha(1.0)
        if self.texture is not None:
            self.mesh.texture(self.texture)

        # Default center if none provided
        self.center = center.copy() if center is not None else np.array([0, 0, 0])

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

    def capture_all_views(
        self,
        output_dir: Union[str, Path],
        image_size: Tuple[int, int] = (1024, 1024),
        show_cap: Optional[bool] = False,
        cmap: np.ndarray = None,
    ) -> None:
        """
        Capture screenshots from all 6 predefined camera views.
        """
        # Estimate a reasonable camera distance from mesh bounds
        center = self.center.copy()
        bounds = self.mesh.bounds()
        camera_distance = {
            "x": (bounds[1] - bounds[0]) * 2.5,
            "y": (bounds[3] - bounds[2]) * 1.75,
            "z": (bounds[5] - bounds[4]) * 2.5,
        }

        # Define a custom camera position based on fiducials (for cap views)
        if show_cap and self.fiducials is not None:
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
        camera_config = HeadCapturer._setup_camera(center, camera_distance)

        # Custom color map
        if cmap is not None:
            self.mesh.cmap("turbo", cmap)

        os.makedirs(output_dir, exist_ok=True)
        screenshot_paths: List[str] = []

        plotter = Plotter(offscreen=True, interactive=False, size=image_size)

        for view_name, view in camera_config["views"].items():
            logging.info(f"Capturing {view['description']}...")

            # Reset scene
            plotter.clear()
            plotter.add(self.mesh)

            # Camera setup
            plotter.camera.SetPosition(view["pos"])
            plotter.camera.SetFocalPoint(camera_config["center"])
            plotter.camera.SetViewUp(view["up"])

            plotter.background((255, 255, 255))
            plotter.render()

            # Save screenshot
            screenshot_path = os.path.join(output_dir, f"{view_name}.png")
            plotter.screenshot(screenshot_path)
            screenshot_paths.append(screenshot_path)

        # plotter.close()
        logging.info(f"All screenshots saved in: {output_dir}")

    @staticmethod
    def capture_single_view(
        mesh: Mesh,
        name: str = None,
        output_dir: Union[str, Path] = None,
        center: np.ndarray = np.array([0.0, 0.0, 0.0]),
        image_size: Tuple[int, int] = (1024, 1024),
        mesh_alpha: Optional[float] = 1.0,
        mesh_color: Optional[str] = None,
        fiducials: Optional[pd.DataFrame] = None,
        bounding_box: Optional[Dict[str, Any]] = None,
        coordinate_vectors: Optional[Dict[str, np.ndarray]] = None,
        cap_plane: Optional[Dict[str, Any]] = None,
        cmap: Optional[np.ndarray] = None,
        curvatures: Optional[List[np.ndarray]] = None,
        show_axes: Optional[bool] = False,
        electrodes: Optional[pd.DataFrame] = None,
    ) -> str:
        """
        Capture a screenshot from a custom single view.
        """
        mesh_copy = mesh.clone()
        bounds = mesh_copy.bounds()

        # Custom view
        view = {
            "pos": [
                center[0] - (bounds[1] - bounds[0]) * 1.25,
                center[1] + (bounds[3] - bounds[2]) * 1.25,
                center[2] + (bounds[5] - bounds[4]) * 3.5,
            ],
            "up": [0, 1, 0],
        }

        # Custom color map
        if cmap is not None:
            mesh_copy.cmap("turbo", cmap)

        plotter = Plotter(offscreen=True, interactive=False, size=image_size)

        # Mesh appearance
        plotter.add(mesh_copy)
        mesh_copy.alpha(mesh_alpha)
        if mesh_color:
            mesh_copy.color(mesh_color)

        # Fiducials
        if fiducials is not None:
            spheres = [Sphere(pos=f, r=6, c="red") for f in fiducials.values]
            plotter.add(spheres)
            # labels = [
            #     Text3D(
            #         l,
            #         pos=f + np.array([5, 5, 5]),
            #         s=8.5,
            #         depth=0.45,
            #         c="black",
            #         font="Theemim",
            #     )
            #     for l, f in fiducials.iterrows()
            # ]
            # plotter.add(labels)

        # Electrodes
        if electrodes is not None:

            def get_color(index):
                if index == "MARKER":
                    return "green"
                elif index == "ELECTRODE":
                    return "red"
                elif index == "ELECTRODE_BASIC":
                    return "blue"
                return "black"

            spheres = [Sphere(pos=f, r=4, c=get_color(idx)) for idx, f in electrodes.iterrows()]
            plotter.add(spheres)

        # Bounding box planes
        if bounding_box:
            x_size, y_size, z_size = bounding_box["size"]
            margin = 0.025
            faces = [
                (
                    [0, 1, 0],
                    [0, y_size / 2, 0],
                    (z_size * (1 - margin), x_size * (1 - margin)),
                ),
                (
                    [0, -1, 0],
                    [0, -y_size / 2, 0],
                    (z_size * (1 - margin), x_size * (1 - margin)),
                ),
                (
                    [1, 0, 0],
                    [x_size / 2, 0, 0],
                    (z_size * (1 - margin), y_size * (1 - margin)),
                ),
                (
                    [-1, 0, 0],
                    [-x_size / 2, 0, 0],
                    (z_size * (1 - margin), y_size * (1 - margin)),
                ),
                (
                    [0, 0, 1],
                    [0, 0, z_size / 2],
                    (x_size * (1 - margin), y_size * (1 - margin)),
                ),
                (
                    [0, 0, -1],
                    [0, 0, -z_size / 2],
                    (x_size * (1 - margin), y_size * (1 - margin)),
                ),
            ]
            planes = [
                Plane(pos=center + np.array(offset), normal=normal, s=size)
                .alpha(0.25)
                .color("gray")
                for normal, offset, size in faces
            ]
            plotter.add(planes)

        # Coordinate vectors
        if coordinate_vectors:
            plotter.add(Sphere(pos=center, r=10, c="black"))
            plotter.add(Arrow(center, center + coordinate_vectors["x"] * 90.0, c="red", s=0.75))
            plotter.add(Arrow(center, center + coordinate_vectors["y"] * 75.0, c="green", s=0.75))
            plotter.add(Arrow(center, center + coordinate_vectors["z"] * 75.0, c="blue", s=0.75))

        # Show cap plane
        if cap_plane is not None and fiducials is not None:
            default_x_size = bounds[1] - bounds[0]
            default_z_size = bounds[5] - bounds[4]
            center, normal = cap_plane["center"].copy(), cap_plane["normal"]

            plane_center = center.copy()  # fallback if fiducials not available
            x_size_temp, z_size_temp = default_x_size, default_z_size

            required_labels = ["NAS", "INI", "LPA", "RPA"]
            if set(required_labels).issubset(fiducials.index):
                # Extract fiducial coordinates safely
                fids = {
                    label: fiducials.loc[label].to_numpy(dtype=float) for label in required_labels
                }

                nas, ini, lpa, rpa = fids["NAS"], fids["INI"], fids["LPA"], fids["RPA"]

                # Plane dimensions based on fiducials
                x_size_temp = abs(lpa[0] - rpa[0])
                z_size_temp = abs(nas[2] - ini[2])

                # Plane center as midpoints
                plane_center = np.mean([nas, lpa, rpa], axis=0)

                # Adjust center.y to account for cropped mesh height
                center[1] = (bounds[3] - plane_center[2]) / 2.0

            # Scale factors for making plane roughly square
            square_scale = 0.75
            x_size = x_size_temp * square_scale + z_size_temp
            z_size = z_size_temp * square_scale + x_size_temp

            # Build and add visualization plane
            plane = Plane(pos=plane_center, normal=normal, s=(z_size, x_size), alpha=0.3).c("red")
            plotter.add(plane)

        # Electrode candidates based on curvature
        if curvatures:
            spheres = [Sphere(pos=c, r=1, c="red") for c in curvatures]
            plotter.add(spheres)

        # Global axes
        if show_axes:
            plotter.add(Axes(mesh_copy, xtitle="X", ytitle="Y", ztitle="Z"))

        # Camera setup
        plotter.camera.SetPosition(view["pos"])
        plotter.camera.SetFocalPoint(center)
        plotter.camera.SetViewUp(view["up"])

        plotter.background((255, 255, 255))
        plotter.render()

        if name and output_dir:
            # Save screenshot
            os.makedirs(output_dir, exist_ok=True)
            screenshot_path = os.path.join(output_dir, f"{name}.png")
            plotter.screenshot(screenshot_path)
            # plotter.close()

            logging.info(f"Captured screenshot: {screenshot_path}")
            return screenshot_path

        # Return image
        image = plotter.screenshot(filename=None, asarray=True)
        # plotter.close()
        return image
