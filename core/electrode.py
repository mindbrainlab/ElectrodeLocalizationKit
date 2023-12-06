import pandas as pd
import numpy as np

from typing import Union, List, Tuple, Optional

from dataclasses import dataclass

@dataclass
class Electrode:
    coordinates: Union[np.ndarray, List[float], Tuple[float, ...]]
    modality: Optional[str] = None
    eID: Union[int, str, None] = None
    label: Optional[str] = None
    _theta: Optional[float] = None
    _phi: Optional[float] = None

    @property
    def keys(self):
        return ('eID', 'coordinates', 'modality', 'label')
    
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
    
    @property 
    def df(self) -> pd.DataFrame:
        """Returns a DataFrame with the electrode's data."""
        df = pd.DataFrame({
                "eID": self.eID,
                "x": self.coordinates[0],
                "y": self.coordinates[1],
                "z": self.coordinates[2],
                "theta": self._theta,
                "phi": self._phi,
                "modality": self.modality,
                "label": self.eID if self.label is None else self.label,
            }, index=[0])
        return df
    
    def __getitem__(self, item):
        return getattr(self, item)
    
    def __setitem__(self, item, value):
        setattr(self, item, value)
    
def compute_distance_between_electrodes(coordinates_1: np.ndarray, coordinates_2: np.ndarray) -> float:
    """Returns the distance between two electrodes."""
    return np.linalg.norm(coordinates_1-coordinates_2)