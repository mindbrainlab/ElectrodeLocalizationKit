import vedo as vd
from abc import ABC, abstractmethod
import vedo as vd
import numpy as np

from config.colors import HeadModelColors
from config.mappings import ModalitiesMapping

from processor.surface_registrator import BaseSurfaceRegistrator
from utils.mesh import normalize_mesh, rescale_to_original_size
from data.data_loader import load_head_surface_mesh_from_file, load_mri_surface_mesh_from_file

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
        
        self.mesh = load_head_surface_mesh_from_file(surface_file)
        
        self.modality = ModalitiesMapping.HEADSCAN
        self.fiducials = []
        
        self.normalization_scale = 1
        
        self.normalize()
        
        self.apply_texture()
            
    def normalize(self):
        self.normalization_scale = normalize_mesh(self.mesh) # type: ignore
        
    def rescale_to_original_size(self):
        self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale) # type: ignore
    
    def apply_texture(self):
        if self.texture_file is not None:
            self.mesh = self.mesh.texture(self.texture_file) # type: ignore
            
    def register_mesh(self, surface_registrator: BaseSurfaceRegistrator) -> np.ndarray:
        transform_matrix = surface_registrator.register() # type: ignore
        self.apply_texture()
        return transform_matrix
    
    def undo_registration(self, surface_registrator: BaseSurfaceRegistrator) -> np.ndarray | None:
        transform_matrix = surface_registrator.undo()
        return transform_matrix
        
        
class MRIScan(BaseHeadModel):
    def __init__(self, mri_file: str):
        
        self.mesh = load_mri_surface_mesh_from_file(mri_file)
        
        self.normalize()

        self.mesh.color(HeadModelColors.MRI_SURFACE_COLOR) # type: ignore
        
        self.modality = ModalitiesMapping.MRI
        
        self.fiducials = []
        
    def normalize(self):
        self.normalization_scale = normalize_mesh(self.mesh)
        
    def rescale_to_original_size(self):
        self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale)
        
    def register_mesh(self, transformation):
        pass
    
    
class UnitSphere(BaseHeadModel):
    def __init__(self):
        self.mesh = vd.Sphere(pos = (0, 0, 0), r = 1.0, res = 24, c = HeadModelColors.LABELING_SPHERE_COLOR)
        self.modality = 'reference'
        self.fiducials = []
        
    def normalize(self):
        pass
    
    def rescale_to_original_size(self):
        pass
    
    def register_mesh(self, transformation):
        pass