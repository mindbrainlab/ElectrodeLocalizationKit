from abc import ABC, abstractmethod
from typing import Union, List
import numpy as np
import cv2 as cv
import vedo as vd

from core.electrode import Electrode

from utils.texture_processing import compute_difference_of_gaussians, compute_hough_circles

class BaseElectrodeDetector(ABC):
    
    @abstractmethod
    def detect_electrodes(self) -> List[Electrode]:
        pass
    

class DogHoughElectrodeDetector(BaseElectrodeDetector):
    def __init__(self, texture_file: str):
        self.texture_file = texture_file
        self.texture = cv.imread(texture_file)

        self.dog = None
        self.circles = None
        self.electrodes = []
        
        self.modality = 'scan'

    def get_difference_of_gaussians(self,
                                    ksize: int = 35,
                                    sigma: float = 12,
                                    F: float = 1.1,
                                    threshold_level: int = 1) -> np.ndarray:
        
        self.dog = compute_difference_of_gaussians(self.texture,
                                                   ksize,
                                                   sigma,
                                                   F,
                                                   threshold_level)

        return self.dog
    
    def get_hough_circles(self,
                          param1: float = 5,
                          param2: float = 12,
                          min_distance_between_circles: int = 100,
                          min_radius: int = 10,
                          max_radius: int = 30) -> np.ndarray:
        if self.dog is None:
            raise Exception("No DoG image available. Please run diff_of_gaussians() first.")
        
        circles_image, self.circles = compute_hough_circles(
            self.texture,
            self.dog,
            param1,
            param2,
            min_distance_between_circles,
            min_radius,
            max_radius,
            (255, 0, 255))
        
        return circles_image
    
    
    def detect_electrodes(self, mesh: vd.Mesh) -> list[Electrode]:
        for circle in self.circles[0, :]: # type: ignore
            vertex = self._get_vertex_from_pixels((circle[0], circle[1]), mesh, self.texture.shape[0:2])
            self.electrodes.append(Electrode(vertex,
                                             modality=self.modality,
                                             label="None"))
            
        return self.electrodes
                                               
    def _get_vertex_from_pixels(self, pixels: tuple[float, float], mesh: vd.Mesh, image_size) -> np.ndarray:
            # Helper function to get the vertex from the mesh that corresponds to
            # the pixel coordinates
            #
            # Written by: Aleksij Kraljic, October 29, 2023
            
            vertices = mesh.points()
            
            # extract the uv coordinates from the mesh
            uv = mesh.pointdata['material_0']
            
            # convert pixels to uv coordinates
            uv_image = [(pixels[0]+0.5)/image_size[0], 1-(pixels[1]+0.5)/image_size[1]]
            
            # find index of closest point in uv with uv_image
            uv_idx = np.argmin(np.linalg.norm(uv-uv_image, axis=1)) # type: ignore
            
            vertex = vertices[uv_idx] # type: ignore
            
            return vertex