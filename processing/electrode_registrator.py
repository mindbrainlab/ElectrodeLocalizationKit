from abc import ABC, abstractmethod
from math import e
import numpy as np
import vedo as vd
from vedo import utils
import vedo.vtkclasses as vtk

from core.electrode import Electrode
from utils.spatial_processing import compute_umeyama_transformation_matrix

class BaseElectrodeRegistrator(ABC):
    
    @abstractmethod
    def register(self, destination_electrodes: list[Electrode], target_electrodes: list[Electrode]):
        pass
    
    
class RigidElectrodeRegistrator(BaseElectrodeRegistrator):
    def __init__(self,
                 source_electrodes: list[Electrode],
                 target_electrodes: list[Electrode]):
        
        self.source_electrodes = source_electrodes
        self.target_electrodes = target_electrodes
        
    def register(self):
        matching_source_electrodes = []
        for target_electrode in self.target_electrodes:
            for source_electrode in self.source_electrodes:
                if target_electrode.label == source_electrode.label:
                    matching_source_electrodes.append(source_electrode)
                    break
        
        T = compute_umeyama_transformation_matrix(source =
                                                  np.array([e.unit_sphere_cartesian_coordinates
                                                            for e in matching_source_electrodes]),
                                                  target =
                                                  np.array([e.unit_sphere_cartesian_coordinates
                                                            for e in self.target_electrodes]))
        
        for electrode in self.source_electrodes:
            source_vector = electrode.unit_sphere_cartesian_coordinates
            source_vector = np.append(source_vector, 1)
            transformed_vector = np.dot(T, source_vector)
            electrode.coordinates = transformed_vector[:3]