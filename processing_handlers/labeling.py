import numpy as np

from data_models.cap_model import CapModel
from data_models.electrode import Electrode

from processing_models.electrode_registrator import BaseElectrodeRegistrator
from processing_models.electrode_aligner import (
    BaseElectrodeLabelingAligner,
    compute_electrode_correspondence,
)
from ui.callbacks.refresh import refresh_count_indicators

from PyQt6.QtWidgets import QPushButton

from utils.spatial import compute_distance_between_coordinates

from config.mappings import ModalitiesMapping

from ui.callbacks.display import display_surface

from PyQt6.QtWidgets import QSlider, QLabel

from utils.warnings import throw_electrode_registration_warning


def register_reference_electrodes_to_measured(
    views: dict, model: CapModel, electrode_registrator: BaseElectrodeRegistrator, ui
):
    model.compute_centroid()

    labeled_measured_electrodes = model.get_labeled_electrodes(
        [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
    )

    if len(labeled_measured_electrodes) < 3:
        throw_electrode_registration_warning()
        return

    reference_electrodes = model.get_electrodes_by_modality([ModalitiesMapping.REFERENCE])

    electrode_registrator.register(
        source_electrodes=reference_electrodes,
        target_electrodes=labeled_measured_electrodes,
    )

    display_surface(views["labeling_reference"])
    ui.label_register_button.setEnabled(False)
    ui.label_align_button.setEnabled(True)

    refresh_count_indicators(
        model,
        ui.measured_electrodes_label,
        ui.labeled_electrodes_label,
        ui.reference_electrodes_label,
        ui.interpolated_electrodes_label,
    )


def align_reference_electrodes_to_measured(
    model: CapModel, views: dict, electrode_aligner: BaseElectrodeLabelingAligner, ui
):
    labeled_measured_electrodes = model.get_labeled_electrodes(
        [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
    )
    reference_electrodes = model.get_electrodes_by_modality([ModalitiesMapping.REFERENCE])

    measured_electrodes_matching_reference_labels = []
    for labeled_electrode in labeled_measured_electrodes:
        for reference_electrode in reference_electrodes:
            if labeled_electrode.label == reference_electrode.label:
                # TODO: missing a check for unique labels
                measured_electrodes_matching_reference_labels.append(labeled_electrode)

    # check if all labels are unique
    assert len(
        set([electrode.label for electrode in measured_electrodes_matching_reference_labels])
    ) == len([electrode.label for electrode in measured_electrodes_matching_reference_labels])

    electrode_aligner.set_source_electrodes(reference_electrodes)
    for electrode in measured_electrodes_matching_reference_labels:
        if electrode.label is not None:
            electrode_aligner.align(electrode)

    display_surface(views["labeling_reference"])
    ui.label_align_button.setEnabled(False)
    ui.label_autolabel_button.setEnabled(True)

    refresh_count_indicators(
        model,
        ui.measured_electrodes_label,
        ui.labeled_electrodes_label,
        ui.reference_electrodes_label,
        ui.interpolated_electrodes_label,
    )


def autolabel_measured_electrodes(
    model: CapModel, views: dict, electrode_aligner: BaseElectrodeLabelingAligner, ui
):
    thresholds = np.arange(0.1, 0.5, 0.05)

    for threshold in thresholds:
        model.correspondence = compute_electrode_correspondence(
            labeled_reference_electrodes=model.get_unaligned_electrodes(
                [ModalitiesMapping.REFERENCE]
            ),
            unlabeled_measured_electrodes=model.get_unlabeled_electrodes(
                [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
            ),
            factor_threshold=threshold,
        )

        label_corresponding_electrodes(model, views, electrode_aligner, ui)

    display_surface(views["labeling_main"])
    display_surface(views["labeling_reference"])

    ui.label_interpolate_button.setEnabled(True)
    ui.label_autolabel_button.setEnabled(False)

    refresh_count_indicators(
        model,
        ui.measured_electrodes_label,
        ui.labeled_electrodes_label,
        ui.reference_electrodes_label,
        ui.interpolated_electrodes_label,
    )


def visualize_labeling_correspondence(model: CapModel, views: dict, ui):
    def f(x: float, k: float = 0.0088, n: float = 0.05):
        return k * x + n

    x = ui.correspondence_slider.value()
    correspondence_value = f(x)
    ui.correspondence_slider_label.setText(f"Value: {correspondence_value:.2f}")

    model.correspondence = compute_electrode_correspondence(
        labeled_reference_electrodes=model.get_unaligned_electrodes([ModalitiesMapping.REFERENCE]),
        unlabeled_measured_electrodes=model.get_unlabeled_electrodes(
            [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
        ),
        factor_threshold=correspondence_value,
    )

    display_pairs = []
    for entry in model.correspondence:
        # unlabeled_electrode = self.model.get_electrode_by_object_id(entry["electrode_id"])
        unlabeled_electrode = entry["electrode"]
        reference_electrode = model.get_electrode_by_label_and_modality(
            entry["suggested_label"], ModalitiesMapping.REFERENCE
        )
        display_pairs.append((unlabeled_electrode, reference_electrode))

    if views["labeling_reference"] is not None:
        views["labeling_reference"].generate_correspondence_arrows(display_pairs)


def label_corresponding_electrodes(
    model: CapModel, views: dict, electrode_aligner: BaseElectrodeLabelingAligner, ui
):
    for entry in model.correspondence:
        unlabeled_electrode = entry["electrode"]
        reference_electrode = model.get_electrode_by_label_and_modality(
            entry["suggested_label"], ModalitiesMapping.REFERENCE
        )
        if unlabeled_electrode is not None and reference_electrode is not None:
            unlabeled_electrode.label = reference_electrode.label
            unlabeled_electrode.labeled = True

    align_reference_electrodes_to_measured(model, views, electrode_aligner, ui)

    refresh_count_indicators(
        model,
        ui.measured_electrodes_label,
        ui.labeled_electrodes_label,
        ui.reference_electrodes_label,
        ui.interpolated_electrodes_label,
    )


def interpolate_missing_electrodes(model: CapModel, views: dict, ui):
    measured_electrodes = model.get_electrodes_by_modality([ModalitiesMapping.HEADSCAN])
    reference_electrodes = model.get_electrodes_by_modality([ModalitiesMapping.REFERENCE])

    measured_labels = set([electrode.label for electrode in measured_electrodes])
    reference_labels = set([electrode.label for electrode in reference_electrodes])
    missing_electrodes = set.difference(reference_labels, measured_labels)

    for label in missing_electrodes:
        reference_electrode = model.get_electrode_by_label_and_modality(
            label, ModalitiesMapping.REFERENCE
        )
        closest_measured_electrodes = sorted(
            measured_electrodes,
            key=lambda electrode: compute_distance_between_coordinates(
                electrode.unit_sphere_cartesian_coordinates,
                reference_electrode.unit_sphere_cartesian_coordinates,  # type: ignore
            ),
        )[:3]

        mean_radius = np.mean(
            [
                np.linalg.norm(electrode.coordinates - electrode.cap_centroid)
                for electrode in closest_measured_electrodes
            ]
        )
        interpolated_electrode_coordinates = (
            mean_radius * reference_electrode.unit_sphere_cartesian_coordinates  # type: ignore
        )  # type: ignore
        electrode = Electrode(
            coordinates=interpolated_electrode_coordinates
            + closest_measured_electrodes[0].cap_centroid,  # type: ignore
            modality=ModalitiesMapping.HEADSCAN,
            label=label,
            labeled=True,
            interpolated=True,
        )
        electrode.interpolated_unit_sphere_coordinates = (
            reference_electrode.unit_sphere_cartesian_coordinates  # type: ignore
        )
        model.insert_electrode(electrode)
    display_surface(views["labeling_main"])
    display_surface(views["labeling_reference"])
    ui.label_interpolate_button.setEnabled(False)

    refresh_count_indicators(
        model,
        ui.measured_electrodes_label,
        ui.labeled_electrodes_label,
        ui.reference_electrodes_label,
        ui.interpolated_electrodes_label,
    )
