from abc import ABC, abstractmethod
from re import A
import numpy as np

from model.electrode import Electrode
from utils.spatial import compute_angular_distance, compute_rotation_axis, align_vectors
from config.electrode_labeling import ElasticAlignmentParameters


class BaseElectrodeLabelingAligner(ABC):

    @abstractmethod
    def set_source_electrodes(self, source_electrodes: list[Electrode]):
        pass

    @abstractmethod
    def align(self, target_electrode: Electrode):
        pass


class ElasticElectrodeAligner(BaseElectrodeLabelingAligner):
    """
    ElasticElectrodeAligner class is responsible for aligning electrodes based on the
    elastic alignment method.
    """

    def __init__(
        self,
        cutoff_deg: float = ElasticAlignmentParameters.cutoff_deg,
        slope: float = ElasticAlignmentParameters.slope,
    ):

        self.source_electrodes = []
        self.cutoff_deg = cutoff_deg
        self.slope = slope

    def set_source_electrodes(self, source_electrodes: list[Electrode]):
        self.source_electrodes = source_electrodes

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

            angle_between_vectors = compute_angular_distance(
                source_vector, target_vector
            )
            rotation_axis = compute_rotation_axis(source_vector, target_vector)

            # compute angular distance vector to all other source electrodes
            attenuation = self._compute_alignment_attenuation_vector(source_electrode)

            # register the source electrode to the target electrode (simply move it there)
            source_electrode.spherical_coordinates = (
                target_electrode.spherical_coordinates
            )
            source_electrode.registered = True

            # apply the adjustment to every non-aligned electrode
            for i, electrode in enumerate(self.source_electrodes):
                if not electrode.registered:
                    electrode.unit_sphere_cartesian_coordinates = align_vectors(
                        electrode.unit_sphere_cartesian_coordinates,
                        rotation_axis,
                        angle_between_vectors,
                        attenuation[i],
                    )

    def _compute_alignment_attenuation_vector(
        self, target_electrode: Electrode
    ) -> np.ndarray:
        # compute the angular distance from every electrode to the target electrode
        D = np.zeros(len(self.source_electrodes))
        target_vector = target_electrode.unit_sphere_cartesian_coordinates
        for i, electrode in enumerate(self.source_electrodes):
            source_vector = electrode.unit_sphere_cartesian_coordinates
            # -- compute the angle between the two vectors
            D[i] = compute_angular_distance(target_vector, source_vector)

        # convert D to degrees
        D = np.degrees(D)

        return 1 / (1 + np.exp(-self.slope * (self.cutoff_deg - D)))


def compute_electrode_correspondence(
    labeled_reference_electrodes: list[Electrode],
    unlabeled_measured_electrodes: list[Electrode],
    factor_threshold: float = 1,
):

    def remove_multiple_correspondeces(correspondence):
        all_labels = [e["suggested_label"] for e in correspondence]
        unique_labels = list(set(all_labels))

        for label in unique_labels:
            label_correspondence = [
                e for e in correspondence if e["suggested_label"] == label
            ]
            if len(label_correspondence) > 1:
                label_correspondence = sorted(
                    label_correspondence, key=lambda x: x["factor"]
                )
                for i in range(1, len(label_correspondence)):
                    correspondence.remove(label_correspondence[i])

        return correspondence

    correspondence = []
    for unlabeled_electrode in unlabeled_measured_electrodes:
        distances = {}

        for reference_electrode in labeled_reference_electrodes:
            distances[reference_electrode.label] = compute_angular_distance(
                unlabeled_electrode.unit_sphere_cartesian_coordinates,
                reference_electrode.unit_sphere_cartesian_coordinates,
            )

        sorted_distance_vector = dict(
            sorted(distances.items(), key=lambda item: item[1])
        )
        sorted_distances = list(sorted_distance_vector.values())
        sorted_labels = list(sorted_distance_vector.keys())

        correspondence_factor = sorted_distances[0] / (
            sorted_distances[0] + sorted_distances[1]
        )

        if correspondence_factor < factor_threshold:
            correspondence_entry = {}
            correspondence_entry["electrode"] = unlabeled_electrode
            correspondence_entry["factor"] = correspondence_factor
            correspondence_entry["suggested_label"] = sorted_labels[0]
            correspondence.append(correspondence_entry)

    return remove_multiple_correspondeces(correspondence)
