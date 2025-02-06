from abc import ABC, abstractmethod
import numpy as np

from data_models.electrode import Electrode
from utils.spatial import compute_umeyama_transformation_matrix


class BaseElectrodeRegistrator(ABC):
    @abstractmethod
    def register(self, source_electrodes: list[Electrode], target_electrodes: list[Electrode]):
        pass


class RigidElectrodeRegistrator(BaseElectrodeRegistrator):
    """
    RigidElectrodeRegistrator is a class that aligns a set of source electrodes
    to a set of target electrodes, using a rigid transformation based on the
    Umeyama algorithm. It matches the electrodes between the two sets based on
    their labels, and then computes the transformation matrix that best aligns
    the source electrodes to the target electrodes.

    Attributes:
    source_electrodes (list[Electrode]): The source electrodes to be aligned.
    target_electrodes (list[Electrode]): The target electrodes to align to.

    Methods:
    register(): Aligns the source electrodes to the target electrodes.
    undo(): Reverts the source electrodes to their original positions.

    Example:
    source_electrodes = [Electrode(label='Fp1', coordinates=(0, 0, 0)),
                         Electrode(label='Fp2', coordinates=(1, 0, 0))]

    target_electrodes = [Electrode(label='Fp1', coordinates=(0, 0, 0)),
                         Electrode(label='Fp2', coordinates=(0, 1, 0))]

    registrator = RigidElectrodeRegistrator(source_electrodes)
    registrator.register(target_electrodes)

    Written by: Aleksij Kraljič, Ljubljana, 2024
    """

    def __init__(self):
        self.source_electrodes = []

    def register(self, source_electrodes: list[Electrode], target_electrodes: list[Electrode]):
        self.source_electrodes = source_electrodes

        # for electrode in self.source_electrodes:
        #     electrode.create_coordinates_snapshot()

        matching_source_electrodes = []
        for target_electrode in target_electrodes:
            for source_electrode in self.source_electrodes:
                if target_electrode.label == source_electrode.label:
                    matching_source_electrodes.append(source_electrode)
                    break

        matching_target_electrodes = []
        for source_electrode in matching_source_electrodes:
            for target_electrode in target_electrodes:
                if target_electrode.label == source_electrode.label:
                    matching_target_electrodes.append(target_electrode)
                    break

        T = compute_umeyama_transformation_matrix(
            source=np.array(
                [e.unit_sphere_cartesian_coordinates for e in matching_source_electrodes]
            ),
            target=np.array(
                [e.unit_sphere_cartesian_coordinates for e in matching_target_electrodes]
            ),
            translate=False,
        )

        for electrode in self.source_electrodes:
            source_vector = electrode.unit_sphere_cartesian_coordinates
            source_vector = np.append(source_vector, 1)
            transformed_vector = np.dot(T, source_vector)
            electrode.coordinates = transformed_vector[:3]
