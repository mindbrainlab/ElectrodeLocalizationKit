import pandas as pd
from collections.abc import Iterable
import numpy as np

from dataclasses import dataclass

@dataclass
class Electrode:
    coordinates: Iterable[float]
    modality: str = None
    ID: int = None
    label: str = None
    spherical_coordinates: Iterable[float] = None

    @property
    def keys(self):
        return ('ID', 'coordinates', 'modality', 'label')
    
    @property
    def spherical_coordinates(self) -> Iterable[float]:
        """Returns the electrode's spherical coordinates."""
        return np.array([self.spherical_coordinates[0], self.spherical_coordinates[1]])
    
    def compute_unit_sphere_spherical_coordinates(self, origin = (0, 0, 0)) -> None:
        """Computes the spherical coordinates of the electrode."""
        x = self.coordinates[0] - origin[0]
        y = self.coordinates[1] - origin[1]
        z = self.coordinates[2] - origin[2]
        r = 1
        theta = np.arccos(z/r)
        phi = np.arctan2(y, x)
        self.spherical_coordinates = np.array([theta, phi])
    
    # @property 
    # def df(self) -> pd.DataFrame:
    #     """Returns a DataFrame with the electrode's data."""
    #     df = pd.DataFrame({
    #             "ID": self.ID,
    #             "x": self.x,
    #             "y": self.y,
    #             "z": self.z,
    #             "theta": self.theta,
    #             "phi": self.phi,
    #             "modality": self.modality,
    #             "label": self.id if self.label is None else self.label,
    #         }, index=[0])
    #     return df
    
def compute_distance_between_electrodes(coordinates_1: Iterable[float], coordinates_2: Iterable[float]) -> float:
    """Returns the distance between two electrodes."""
    return np.linalg.norm(coordinates_1-coordinates_2)