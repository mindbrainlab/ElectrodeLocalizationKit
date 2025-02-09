import pandas as pd
import numpy as np
import vedo as vd

from dataclasses import dataclass

from utils.spatial import (
    compute_unit_spherical_coordinates_from_cartesian,
    compute_cartesian_coordinates_from_unit_spherical,
)


@dataclass
class Electrode:
    coordinates: np.ndarray
    modality: str
    label: str | None = None
    labeled: bool = False
    interpolated: bool = False
    fiducial: bool = False
    _cap_centroid: np.ndarray | None = None
    _mapped_to_unit_sphere: bool = False
    _aligned: bool = False

    @property
    def keys(self):
        return ("coordinates", "modality", "label")

    @property
    def spherical_coordinates(self) -> np.ndarray:
        """Returns the electrode's spherical coordinates."""
        theta, phi = self._compute_unit_sphere_spherical_coordinates()
        return np.array([theta, phi])

    @property
    def unit_sphere_cartesian_coordinates(self) -> np.ndarray:
        """Returns the electrode's cartesian coordinates in the unit sphere."""
        if not self._mapped_to_unit_sphere:
            theta, phi = self._compute_unit_sphere_spherical_coordinates()
            unit_sphere_coordinates = self._compute_unit_sphere_cartesian_coordinates(theta, phi)
        else:
            unit_sphere_coordinates = self.coordinates
        return unit_sphere_coordinates

    @property
    def aligned(self) -> bool:
        return self._aligned

    @aligned.setter
    def aligned(self, value: bool):
        self._aligned = value

    @property
    def cap_centroid(self):
        return self._cap_centroid

    @cap_centroid.setter
    def cap_centroid(self, centroid: np.ndarray):
        self._cap_centroid = centroid

    @spherical_coordinates.setter
    def spherical_coordinates(self, coordinates: np.ndarray):
        """Sets the electrode's spherical coordinates."""
        theta, phi = coordinates
        self.coordinates = self._compute_unit_sphere_cartesian_coordinates(theta, phi)
        self._mapped_to_unit_sphere = True

    @unit_sphere_cartesian_coordinates.setter
    def unit_sphere_cartesian_coordinates(self, coordinates: np.ndarray):
        """Sets the electrode's cartesian coordinates in the unit sphere."""
        self.coordinates = coordinates.copy()
        self._mapped_to_unit_sphere = True

    def _compute_unit_sphere_spherical_coordinates(self) -> tuple[float, float]:
        """Computes the spherical coordinates of the electrode."""
        # compute centroid of the mesh
        if self._cap_centroid is not None:
            origin = self._cap_centroid
        else:
            origin = (0, 0, 0)
        (theta, phi) = compute_unit_spherical_coordinates_from_cartesian(
            list(self.coordinates), origin=origin
        )
        return (theta, phi)

    def _compute_unit_sphere_cartesian_coordinates(self, theta: float, phi: float) -> np.ndarray:
        """Computes the cartesian coordinates of the electrode."""
        (x, y, z) = compute_cartesian_coordinates_from_unit_spherical((theta, phi))
        return np.array([x, y, z])

    def apply_transformation(self, A: np.matrix):
        x = np.array([self.coordinates[0], self.coordinates[1], self.coordinates[2], 1])

        x.shape = (4, 1)
        y4d = A @ x
        y = np.array(y4d[0:3])
        self.coordinates = np.array([c[0] for c in y])

    def project_to_mesh(self, mesh: vd.Mesh):
        """Projects the electrode to the mesh."""
        closest_point = mesh.closest_point(self.coordinates)
        if isinstance(closest_point, np.ndarray):
            self.coordinates = closest_point

    def __eq__(self, other):
        return id(self) == id(other)

    @property
    def df(self) -> pd.DataFrame:
        """Returns a DataFrame with the electrode's data."""
        df = pd.DataFrame(
            {
                "x": self.coordinates[0],
                "y": self.coordinates[1],
                "z": self.coordinates[2],
                "modality": self.modality,
                "label": self.label,
            },
            index=[0],
        )
        return df

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)
