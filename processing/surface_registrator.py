from abc import ABC, abstractmethod
import numpy as np
import vedo as vd

from core.electrode import Electrode

from utils.texture_processing import compute_difference_of_gaussians, compute_hough_circles

class BaseSurfaceRegistrator(ABC):
    
    @abstractmethod
    def register_surfaces(self) -> List[Electrode]:
        pass