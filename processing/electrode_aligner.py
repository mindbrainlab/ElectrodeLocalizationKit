from abc import ABC, abstractmethod
from calendar import c
from math import e
import numpy as np
import vedo as vd
from vedo import utils
import vedo.vtkclasses as vtk

from core.electrode import Electrode
from utils.spatial_processing import compute_umeyama_transformation_matrix

class BaseElectrodeAligner(ABC):
    
    @abstractmethod
    def align(self, electrode_label: str):
        pass
    
    
class ElectrodeAligner(BaseElectrodeAligner):
    def __init__(self,
                 source_electrodes: list[Electrode],
                 target_electrodes: list[Electrode]):
        
        self.source_electrodes = source_electrodes
        self.target_electrodes = target_electrodes
        
    def align(self, electrode_label: str):
        # extract the source electrode with the given label
        for electrode in self.source_electrodes:
            if electrode.label == electrode_label:
                source_electrode = electrode
                break

        # extract the target electrode with the given label
        for electrode in self.target_electrodes:
            if electrode.label == electrode_label:
                target_electrode = electrode
                break

        if not source_electrode.registered:
            # extract the spherical coordinates of the source and target electrodes
            source_vector = source_electrode.unit_sphere_cartesian_coordinates
            target_vector = target_electrode.unit_sphere_cartesian_coordinates

            angle_between_vectors = compute_angular_distance(source_vector, target_vector)
            rotation_axis = compute_rotation_axis(source_vector, target_vector)

            # compute angular distance vector to all other source electrodes
            attenuation = compute_alignment_attenuation_vector(self.source_electrodes,
                                                                source_electrode,
                                                                config={'L': 1, 'x0': 30, 'k': 0.1})

            # register the source electrode to the target electrode (simply move it there)
            source_electrode.spherical_coordinates = target_electrode.spherical_coordinates
            source_electrode.registered = True

            # -- apply the adjustment to every non-registered electrode
            for i, electrode in enumerate(self.source_electrodes):
                if not electrode.registered:
                    electrode.unit_sphere_cartesian_coordinates = align_vectors(
                        electrode.unit_sphere_cartesian_coordinates,
                        rotation_axis,
                        angle_between_vectors,
                        attenuation[i])
                

def compute_alignment_attenuation_vector(electrodes: list[Electrode], 
                                         target_electrode: Electrode,
                                         config={'L': 1, 'x0': 30, 'k': 0.1}) -> np.ndarray:
    # logistic attenuation curve parameters
    L = config['L']
    x0 = config['x0']
    k = config['k']

    # compute the angular distance from every electrode to the target electrode
    D = np.zeros(len(electrodes))
    source_vector = target_electrode.unit_sphere_cartesian_coordinates
    for i, electrode in enumerate(electrodes):
        target_vector = electrode.unit_sphere_cartesian_coordinates
        # -- compute the angle between the two vectors
        D[i] = compute_angular_distance(source_vector, target_vector)
        
    # convert D to degrees
    D = np.degrees(D)

    attenuation = L/(1+np.exp(-k*(x0-D)))
    return attenuation

def compute_angular_distance(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    """
    Computes the angular distance between two vectors in cartesian coordinates.
    TODO: Implement the function to compute the angular distance between two vectors in spherical coordinates.
    """
    return np.arccos(np.dot(vector_a, vector_b)/(np.linalg.norm(vector_a)*np.linalg.norm(vector_b)))

def compute_rotation_axis(vector_a: np.ndarray, vector_b: np.ndarray) -> np.ndarray:
    # compute the rotation axis between the source and target vectors
    e = np.cross(vector_a, vector_b)
    if any(e):
        e = e/np.linalg.norm(e)
    return e

def align_vectors(input_vector, rotation_axis: np.ndarray, rotation_angle: float, attenuation: float = 1):
    # compute the rotation axis between the source and target vectors
    e = rotation_axis
    
    # theta - rotation angle
    theta = rotation_angle*attenuation

    # Q - rotation quaternion
    Q = (np.cos(theta/2), e[0]*np.sin(theta/2), e[1]*np.sin(theta/2), e[2]*np.sin(theta/2))

    R = convert_quaternion_to_rotation_matrix(Q)

    output_vector = (R @ input_vector.T).T
    return output_vector

def convert_quaternion_to_rotation_matrix(Q: tuple[float, float, float, float]) -> np.ndarray:
    # w, x, y, z - quaternion components
    w = Q[0]
    x = Q[1]
    y = Q[2]
    z = Q[3]

    # rotation matrix components
    Rxx = 1 - 2*(y**2 + z**2)
    Rxy = 2*(x*y - z*w)
    Rxz = 2*(x*z + y*w)
    Ryx = 2*(x*y + z*w)
    Ryy = 1 - 2*(x**2 + z**2)
    Ryz = 2*(y*z - x*w )
    Rzx = 2*(x*z - y*w )
    Rzy = 2*(y*z + x*w )
    Rzz = 1 - 2 *(x**2 + y**2)
    R = np.array([[Rxx,    Rxy,    Rxz],
                  [Ryx,    Ryy,    Ryz],
                  [Rzx,    Rzy,    Rzz]])
    return R
