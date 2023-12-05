import vedo as vd
from dataclasses import dataclass
from collections.abc import Iterable

from abc import ABC, abstractmethod, abstractproperty

from .electrode import Electrode

class BaseHeadModel(ABC):
    
    @property
    @abstractmethod
    def mesh(self):
        pass
    
    @property
    @abstractmethod
    def fiducials(self):
        pass
    
    @fiducials.setter
    @abstractmethod
    def fiducials(self, fiducials: Iterable[Electrode]):
        pass
    
    @property
    @abstractmethod
    def modality(self):
        pass
    
    @abstractmethod
    def apply_transformation(self, transformation):
        pass
    

class HeadScan(BaseHeadModel):
    def __init__(self, surface_file: str, texture_file: str = None):
        self._mesh = vd.Mesh(surface_file)
        self._modality = 'scan'
        self._fiducials = []
        
        if texture_file is not None:
            self.apply_texture(texture_file)
        
    @property
    def mesh(self):
        return self._mesh
    
    @property
    def modality(self):
        return self._modality
    
    @property
    def fiducials(self):
        return self._fiducials
    
    @fiducials.setter
    def fiducials(self, fiducials: Iterable[Electrode]):
        self._fiducials = fiducials
        
    def apply_transformation(self, transformation):
        pass
    
    def apply_texture(self, texture_file: str):
        self._mesh = self._mesh.texture(texture_file)
    
# not implemented yet
class MRIScan(BaseHeadModel):
    def __init__(self, mri_file: str):
        self.mesh = None
        self.modality = 'mri'
        self.fiducials = []
    
    @property
    def fiducials(self):
        return self._fiducials
    
    @fiducials.setter
    def fiducials(self, fiducials: Iterable[Electrode]):
        self._fiducials = fiducials
        
    def apply_transformation(self, transformation):
        pass
    
    