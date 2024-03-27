import pandas as pd
import numpy as np
import vedo as vd

from dataclasses import dataclass

from utils.spatial_processing import (compute_unit_spherical_coordinates_from_cartesian,
                                      compute_cartesian_coordinates_from_unit_spherical)

@dataclass
class Electrode:
    coordinates: np.ndarray | list[float] | tuple[float, ...]
    modality: str | None = None
    label: str | None = None
    labeled: bool = False

    @property
    def keys(self):
        return ('coordinates', 'modality', 'label')
    
    @property
    def spherical_coordinates(self) -> np.ndarray:
        """Returns the electrode's spherical coordinates."""
        theta, phi = self._compute_unit_sphere_spherical_coordinates()
        return np.array([theta, phi])
    
    @property
    def unit_sphere_cartesian_coordinates(self) -> np.ndarray:
        """Returns the electrode's cartesian coordinates in the unit sphere."""
        theta, phi = self._compute_unit_sphere_spherical_coordinates()
        unit_sphere_coordinates = self._compute_unit_sphere_cartesian_coordinates(theta, phi)
        return unit_sphere_coordinates
    
    def _compute_unit_sphere_spherical_coordinates(self) -> tuple[float, float]:
        """Computes the spherical coordinates of the electrode."""
        (theta, phi) = compute_unit_spherical_coordinates_from_cartesian(list(self.coordinates),
                                                                         origin = (0, 0, 0))
        return (theta, phi)
        
    def _compute_unit_sphere_cartesian_coordinates(self, theta: float, phi: float) -> np.ndarray:
        """Computes the cartesian coordinates of the electrode."""
        (x, y, z) = compute_cartesian_coordinates_from_unit_spherical((theta, phi))
        return np.array([x, y, z])
        
    def apply_transformation(self, A: np.matrix):
        x = np.array([self.coordinates[0],
                        self.coordinates[1],
                        self.coordinates[2],
                        1])
        
        x.shape = (4, 1)
        y4d = A @ x
        y = np.array(y4d[0:3])
        self.coordinates = y
        
    def project_to_mesh(self, mesh: vd.Mesh):
        """Projects the electrode to the mesh."""
        closest_point = mesh.closest_point(self.coordinates)
        if isinstance(closest_point, np.ndarray):
            self.coordinates = closest_point
        
    
    @property 
    def df(self) -> pd.DataFrame:
        """Returns a DataFrame with the electrode's data."""
        df = pd.DataFrame({
                "x": self.coordinates[0],
                "y": self.coordinates[1],
                "z": self.coordinates[2],
                "modality": self.modality,
                "label": self.label,
            }, index=[0])
        return df
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __setitem__(self, item, value):
        setattr(self, item, value)