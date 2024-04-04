from abc import ABC, abstractmethod
import numpy as np

from model.electrode import Electrode
from utils.spatial import (compute_angular_distance,
                                      compute_rotation_axis,
                                      align_vectors)
from config.electrode_labeling import ElasticAlignmentParameters

class BaseElectrodeLabelingAligner(ABC):
    
    @abstractmethod
    def align(self, electrode_label: str):
        pass
    
    
class ElasticElectrodeAligner(BaseElectrodeLabelingAligner):
    """
    ElasticElectrodeAligner class is responsible for aligning electrodes based on the
    elastic alignment method.
    """
    def __init__(self,
                 source_electrodes: list[Electrode],
                 L: float = ElasticAlignmentParameters.L,
                 x0: float = ElasticAlignmentParameters.x0,
                 k: float = ElasticAlignmentParameters.k):
        
        self.source_electrodes = source_electrodes
        self.L = L
        self.x0 = x0
        self.k = k
        
    def align(self, target_electrode: Electrode):
        # extract the source electrode with the given label
        for electrode in self.source_electrodes:
            if electrode.label == target_electrode.label:
                source_electrode = electrode
                break
        
        # if the source (reference) electrode has not yet been registered, register it
        if not source_electrode.registered:
            # extract the spherical coordinates of the source and target electrodes
            source_vector = source_electrode.unit_sphere_cartesian_coordinates
            target_vector = target_electrode.unit_sphere_cartesian_coordinates

            angle_between_vectors = compute_angular_distance(source_vector, target_vector)
            rotation_axis = compute_rotation_axis(source_vector, target_vector)

            # compute angular distance vector to all other source electrodes
            attenuation = self._compute_alignment_attenuation_vector(source_electrode)

            # register the source electrode to the target electrode (simply move it there)
            source_electrode.spherical_coordinates = target_electrode.spherical_coordinates
            source_electrode.registered = True

            # apply the adjustment to every non-aligned electrode
            for i, electrode in enumerate(self.source_electrodes):
                if not electrode.registered:
                    electrode.unit_sphere_cartesian_coordinates = align_vectors(
                        electrode.unit_sphere_cartesian_coordinates,
                        rotation_axis,
                        angle_between_vectors,
                        attenuation[i])
    
    def _compute_alignment_attenuation_vector(self, target_electrode: Electrode) -> np.ndarray:
        # compute the angular distance from every electrode to the target electrode
        D = np.zeros(len(self.source_electrodes))
        target_vector = target_electrode.unit_sphere_cartesian_coordinates
        for i, electrode in enumerate(self.source_electrodes):
            source_vector = electrode.unit_sphere_cartesian_coordinates
            # -- compute the angle between the two vectors
            D[i] = compute_angular_distance(target_vector, source_vector)
            
        # convert D to degrees
        D = np.degrees(D)

        return self.L/(1+np.exp(-self.k*(self.x0-D)))
                

def compute_electrode_correspondence(reference_electrodes: list[Electrode],
                                     unlabeled_electrodes: list[Electrode],
                                     factor_threshold: float = 0.3):
    correspondence = []
    for unlabeled_electrode in unlabeled_electrodes:
        distances = {}
        
        for reference_electrode in reference_electrodes:
            distances[reference_electrode.label] = compute_angular_distance(unlabeled_electrode.unit_sphere_cartesian_coordinates,
                                                                            reference_electrode.unit_sphere_cartesian_coordinates)
        
        sorted_distance_vector = dict(sorted(distances.items(), key=lambda item: item[1]))
        sorted_distances = list(sorted_distance_vector.values())
        sorted_labels = list(sorted_distance_vector.keys())
        
        correspondence_factor = sorted_distances[0] / (sorted_distances[0] + sorted_distances[1])
        
        if correspondence_factor < factor_threshold:
            correspondence_entry = {}
            correspondence_entry['electrode_id'] = id(unlabeled_electrode)
            correspondence_entry['factor'] = correspondence_factor
            correspondence_entry['suggested_label'] = sorted_labels[0]
            correspondence.append(correspondence_entry)
            
    return correspondence
