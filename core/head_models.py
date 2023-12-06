from re import T
import vedo as vd

from abc import ABC, abstractmethod
from typing import Union, List
import numpy as np

from .electrode import Electrode

import vedo as vd

# class BaseHeadModel(ABC):
    
#     @property
#     @abstractmethod
#     def mesh(self):
#         pass
    
#     @mesh.setter
#     @abstractmethod
#     def mesh(self, mesh: vd.Mesh):
#         pass
    
#     @property
#     @abstractmethod
#     def fiducials(self):
#         pass
    
#     @fiducials.setter
#     @abstractmethod
#     def fiducials(self, fiducials: Union[List[float], np.ndarray]):
#         pass
    
#     @property
#     @abstractmethod
#     def modality(self):
#         pass
    
#     @modality.setter
#     @abstractmethod
#     def modality(self, modality: str):
#         pass
    
#     @abstractmethod
#     def apply_transformation(self, transformation):
#         pass

class HeadScan():
    def __init__(self, surface_file: str, texture_file: str = ""):
        self.surface_file = surface_file
        self.texture_file = texture_file
        self.mesh = vd.Mesh(surface_file)
        self.modality = 'scan'
        self.fiducials = []
        
        if texture_file != "":
            self.apply_texture(texture_file)
        
    def apply_transformation(self, transformation):
        pass
    
    def apply_texture(self, texture_file: str):
        self.mesh = self.mesh.texture(texture_file)
    
# not implemented yet
class MRIScan():
    def __init__(self, mri_file: str):
        self.mesh = vd.Mesh()
        self.modality = 'mri'
        self.fiducials = []
        
    def apply_transformation(self, transformation):
        pass
    
    