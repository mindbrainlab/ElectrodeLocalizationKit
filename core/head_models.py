from re import T
import vedo as vd

from abc import ABC, abstractmethod
from typing import Union, List
import numpy as np

from .electrode import Electrode

import vedo as vd

import nibabel as nib

try:
    import vedo.vtkclasses as vtk
except ImportError:
    import vtkmodules.all as vtk

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
    def __init__(self, surface_file: str, texture_file: str | None = None):
        self.surface_file = surface_file
        self.texture_file = texture_file
        self.mesh = vd.Mesh(surface_file)
        self.modality = 'scan'
        self.fiducials = []
        
        self.normalization_scale = 1
        
        self.normalize()
        
        if texture_file:
            self.apply_texture(texture_file)
            
    def normalize(self):
        self.mesh, self.normalization_scale = normalize_mesh(self.mesh)
        
    def rescale_to_original_size(self):
        self.mesh, self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale)
        
    def apply_transformation(self, transformation):
        pass
    
    def apply_texture(self, texture_file: str):
        self.mesh = self.mesh.texture(texture_file)
    
# not implemented yet
class MRIScan():
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
        self.mesh, self.normalization_scale = normalize_mesh(self.mesh)
        
    def rescale_to_original_size(self):
        self.mesh, self.normalization_scale = rescale_to_original_size(self.mesh, self.normalization_scale)
        
    def apply_transformation(self, transformation):
        pass
    
    
def normalize_mesh(mesh: vd.Mesh) -> tuple[vd.Mesh, float]:
    """Scale Mesh average size to unit."""
    coords = mesh.points()
    coords = np.array(mesh.points())
    if not coords.shape[0]:
        return mesh, 1.0
    cm = np.mean(coords, axis=0)
    pts = coords - cm
    xyz2 = np.sum(pts * pts, axis=0)
    scale = 1 / np.sqrt(np.sum(xyz2) / len(pts))
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(scale, scale, scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    return mesh._update(tf.GetOutput()), scale

def rescale_to_original_size(mesh: vd.Mesh, scale: float) -> tuple[vd.Mesh, float]:
    """Rescale Mesh to original size."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(1/scale, 1/scale, 1/scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    return mesh._update(tf.GetOutput()), 1.0