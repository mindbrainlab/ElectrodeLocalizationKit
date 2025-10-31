import logging
import numpy as np
import pandas as pd

from typing import Dict, List, Optional, Tuple
from vedo import Arrow, Axes, Mesh, Plotter, Sphere, settings


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HeadPoseAligner:
    def __init__(
        self,
        mesh: Mesh,
        fiducials: pd.DataFrame,
        texture: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize the head pose aligner.
        """
        self.mesh = mesh.clone()
        self.fiducials = fiducials.copy()
        self.texture = texture.copy() if texture is not None else None

        self.origin = None
        self.source_origin = None
        self.rotation_matrix = None
        self.coordinate_vectors = None

    def _get_fiducials(self, required_list) -> List[np.ndarray]:
        """
        Extract fiducials and validate they exist.
        """
        for fid in required_list:
            if fid not in self.fiducials.index:
                raise ValueError(f"Required fiducial {fid} not found")

        return [self.fiducials.loc[fid].to_numpy().astype(float).copy() for fid in required_list]

    def _calculate_origin(self) -> np.ndarray:
        """
        Calculate head center as centroid of key anatomical landmarks.
        """
        required_for_origin = ["NAS", "LPA", "RPA", "INI"]
        nas, lpa, rpa, ini = self._get_fiducials(required_for_origin)
        return (nas + lpa + rpa + ini) / 4.0

    @staticmethod
    def _rodrigues_rotation_matrix(axis, angle):
        """
        Create rotation matrix using Rodrigues' rotation formula.
        """
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)

        # Cross-product matrix for rotation axis
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])

        # Rodrigues' formula: R = I + sin(θ)K + (1-cos(θ))K²
        rotation_matrix = np.eye(3) + sin_angle * K + (1 - cos_angle) * np.dot(K, K)

        return rotation_matrix

    def _calculate_orientation_matrix(
        self,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """
        Compute a rotation matrix that orients the head into a standardized anatomical coordinate system facing forward and horizontally aligned.
        Standard coordinate system after transformation:
        - X-axis: Left to Right (positive X = right)
        - Y-axis: Bottom to Top (positive Y = up)
        - Z-axis: Back to Front (positive Z = forward/anterior)
        """
        # Validate required fiducials
        required = ["NAS", "INI", "LPA", "RPA"]
        nas, ini, lpa, rpa = self._get_fiducials(required)

        # Calculate origin (centroid of key fiducials)
        origin = self._calculate_origin()
        logging.info(f"Origin: {origin}")

        # Step 1: Align face to look forward (Z-axis)
        # Calculate the INI to NAS vector (current face direction)
        # face_direction = nas - ini
        # face_direction = face_direction / np.linalg.norm(face_direction)
        plane_center = np.mean([lpa, rpa], axis=0)
        face_direction = nas - [ini[0], plane_center[1], ini[2]]
        face_direction = face_direction / np.linalg.norm(face_direction)

        # Target direction is positive z-axis (forward)
        target_z = np.array([0, 0, 1])

        # Calculate rotation matrix to align face_direction with z-axis
        if np.allclose(face_direction, target_z):
            # Already aligned
            rotation_matrix_1 = np.eye(3)
        elif np.allclose(face_direction, -target_z):
            # Opposite direction, need 180-degree rotation
            if abs(face_direction[2]) > 0.9:
                rotation_axis = np.array([0, 1, 0])
            else:
                rotation_axis = np.array([1, 0, 0])
            angle = np.pi
            rotation_matrix_1 = self._rodrigues_rotation_matrix(rotation_axis, angle)
        else:
            # General case: calculate rotation axis and angle
            rotation_axis = np.cross(face_direction, target_z)
            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            angle = np.arccos(np.clip(np.dot(face_direction, target_z), -1.0, 1.0))
            rotation_matrix_1 = self._rodrigues_rotation_matrix(rotation_axis, angle)

        # Step 2: Align horizontally (Y-axis)
        # Apply first rotation to the horizontal reference points
        left_rotated = rotation_matrix_1 @ (lpa - origin)
        right_rotated = rotation_matrix_1 @ (rpa - origin)

        # Calculate the Y-difference between left and right points
        y_diff = left_rotated[1] - right_rotated[1]

        # Calculate the horizontal distance between points (X-Z plane)
        horizontal_distance = np.sqrt(
            (left_rotated[0] - right_rotated[0]) ** 2 + (left_rotated[2] - right_rotated[2]) ** 2
        )

        # Check if points are too close horizontally (degenerate case)
        if horizontal_distance < 1e-6:
            logging.warning(
                "Left and right reference points are vertically aligned. Skipping horizontal alignment."
            )
            rotation_matrix_2 = np.eye(3)
        else:
            # Calculate the tilt angle around Z-axis
            # We want to rotate so that the Y-difference becomes zero
            tilt_angle = np.arctan2(y_diff, horizontal_distance)

            # Create rotation matrix around Z-axis to remove the tilt
            # Negative angle because we want to counter-rotate the tilt
            rotation_matrix_2 = self._rodrigues_rotation_matrix(np.array([0, 0, 1]), -tilt_angle)

        # Combine both rotations: first forward alignment, then horizontal alignment
        rotation_matrix = rotation_matrix_2 @ rotation_matrix_1

        # Calculate the new coordinate system vectors after rotation
        x_axis = rotation_matrix @ np.array([1, 0, 0])  # Right direction
        y_axis = rotation_matrix @ np.array([0, 1, 0])  # Up direction
        z_axis = rotation_matrix @ np.array([0, 0, 1])  # Forward direction

        # Create coordinate vectors dictionary
        coordinate_vectors = {
            "x": x_axis,
            "y": y_axis,
            "z": z_axis,
        }

        return origin, coordinate_vectors, rotation_matrix

    def visualize_orientation(
        self,
        mesh_alpha: float = 0.25,
    ):
        """
        Visualize oriented head mesh with fiducials and coordinate axes.
        """
        plotter = Plotter(title="Head Orientation", size=(1200, 800))

        # Mesh appearance
        self.mesh.alpha(mesh_alpha)
        if self.texture is None:
            self.mesh.color("black").alpha(0.25)
        plotter.add(self.mesh)

        # Fiducials
        if self.fiducials is not None:
            fiducial_spheres = [
                Sphere(pos=fiducial, r=2.5, c="red") for fiducial in self.fiducials.values
            ]
            plotter.add(fiducial_spheres)

        if mesh_alpha < 1.0 and self.origin is not None and self.coordinate_vectors is not None:
            # Mark origin
            plotter.add(Sphere(pos=self.origin, r=10, c="black"))

            # Coordinate system arrows
            plotter.add(
                Arrow(
                    self.origin,
                    self.origin + self.coordinate_vectors["x"] * 75.0,
                    c="red",
                    s=0.5,
                )
            )
            plotter.add(
                Arrow(
                    self.origin,
                    self.origin + self.coordinate_vectors["y"] * 75.0,
                    c="green",
                    s=0.5,
                )
            )
            plotter.add(
                Arrow(
                    self.origin,
                    self.origin + self.coordinate_vectors["z"] * 75.0,
                    c="blue",
                    s=0.5,
                )
            )

        # Global axes
        axes_actor = Axes(self.mesh, xtitle="X (Right)", ytitle="Y (Up)", ztitle="Z (Forward)")
        plotter.add(axes_actor)

        plotter.show()

        # Reset mesh alpha
        self.mesh.alpha(1.0)

    def orient_head_mesh(
        self,
        show_result: bool = False,
    ) -> Tuple[Mesh, pd.DataFrame]:
        """
        Orient the head mesh and fiducials into standard coordinate space.
        """
        if self.mesh is None:
            raise ValueError("Mesh is not loaded")
        if self.fiducials is None or self.fiducials.empty:
            raise ValueError("Fiducials are not loaded")

        # Calculate orientation
        self.source_origin, self.coordinate_vectors, self.rotation_matrix = (
            self._calculate_orientation_matrix()
        )

        # Apply transformation to mesh (translate then rotate)
        mesh_vertices = self.mesh.points().copy()
        transformed_vertices = (mesh_vertices - self.source_origin) @ self.rotation_matrix.T
        self.mesh.points(transformed_vertices)

        # Apply same transformation to fiducials
        fiducial_coords = self.fiducials.to_numpy()
        transformed_fiducials = (fiducial_coords - self.source_origin) @ self.rotation_matrix.T
        self.fiducials = pd.DataFrame(
            transformed_fiducials,
            index=self.fiducials.index,
            columns=self.fiducials.columns,
        )

        # Update origin
        self.origin = self._calculate_origin()

        # Optional visualization
        if show_result:
            self.visualize_orientation()

        return self.mesh, self.fiducials
