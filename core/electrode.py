import pandas as pd
import numpy as np
import vedo as vd

from dataclasses import dataclass

@dataclass
class Electrode:
    coordinates: np.ndarray | list[float] | tuple[float, ...]
    modality: str | None = None
    label: str | None = None
    labeled: bool = False
    _theta: float | None = None
    _phi: float | None = None

    @property
    def keys(self):
        return ('coordinates', 'modality', 'label')
    
    @property
    def spherical_coordinates(self) -> np.ndarray:
        """Returns the electrode's spherical coordinates."""
        if self._theta is None or self._phi is None:
            self.compute_unit_sphere_spherical_coordinates()
        return np.array([self._theta, self._phi])
    
    def compute_unit_sphere_spherical_coordinates(self, origin = (0, 0, 0)) -> None:
        """Computes the spherical coordinates of the electrode."""
        x = self.coordinates[0] - origin[0]
        y = self.coordinates[1] - origin[1]
        z = self.coordinates[2] - origin[2]
        r = 1
        self.theta = np.arccos(z/r)
        self.phi = np.arctan2(y, x)
        
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
                "theta": self._theta,
                "phi": self._phi,
                "modality": self.modality,
                "label": self.label,
            }, index=[0])
        return df
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __setitem__(self, item, value):
        setattr(self, item, value)