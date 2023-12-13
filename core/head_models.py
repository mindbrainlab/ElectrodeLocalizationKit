import vedo as vd
from abc import ABC, abstractmethod
import numpy as np
import vedo as vd
import nibabel as nib

from processing.surface_registrator import BaseSurfaceRegistrator
from utils.spatial_processing import normalize_mesh, rescale_to_original_size

try:
    import vedo.vtkclasses as vtk
except ImportError:
    import vtkmodules.all as vtk

class BaseHeadModel(ABC):
    
    @abstractmethod
    def normalize(self):
        pass
        
    def rescale_to_original_size(self):
        pass
            
    def register_mesh(self, transformation):
        pass

class HeadScan(BaseHeadModel):
    def __init__(self, surface_file: str, texture_file: str | None = None):
        self.surface_file = surface_file
        self.texture_file = texture_file
        self.mesh = vd.Mesh(surface_file)
        self.modality = 'scan'
        self.fiducials = []
        
        self.normalization_scale = 1
        
        self.normalize()
        
        self.original_mesh = None
        
        self.apply_texture()
            
    def normalize(self):
        self.normalization_scale = normalize_mesh(self.mesh) # type: ignore
        
    def rescale_to_original_size(self):
        self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale) # type: ignore
    
    def apply_texture(self):
        if self.texture_file is not None:
            self.mesh = self.mesh.texture(self.texture_file) # type: ignore
            
    def register_mesh(self, surface_registrator: BaseSurfaceRegistrator):
        self.original_mesh = self.mesh.clone()
        lmt = surface_registrator.register(self.mesh) # type: ignore
        self.apply_texture()
        return lmt
    
    def revert_registration(self):
        if self.original_mesh is not None:
            self.mesh = self.original_mesh.clone()
            self.original_mesh = None
        
    
# not implemented yet
class MRIScan(BaseHeadModel):
    def __init__(self, mri_file: str):
        
        img = nib.load(mri_file)                                                 # type: ignore
        
        verts = img.darrays[0].data                                              # type: ignore
        cells = img.darrays[1].data                                              # type: ignore
        
        self.mesh = vd.Mesh([verts, cells])
        
        self.normalize()

        self.mesh.color((170, 170, 170)) # type: ignore
        
        self.modality = 'mri'
        
        self.fiducials = []
        
    def normalize(self):
        self.normalization_scale = normalize_mesh(self.mesh)
        
    def rescale_to_original_size(self):
        self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale)
        
    def register_mesh(self, transformation):
        pass