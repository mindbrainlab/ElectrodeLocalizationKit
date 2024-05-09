from model.cap_model import CapModel

from processor.electrode_registrator import BaseElectrodeRegistrator
from processor.electrode_aligner import (
    BaseElectrodeLabelingAligner,
    compute_electrode_correspondence,
)

from config.mappings import ModalitiesMapping

from ui.callbacks.display import display_surface

from PyQt6.QtWidgets import QSlider, QLabel


def register_reference_electrodes_to_measured(
    views: dict,
    status: dict,
    model: CapModel,
    electrode_registrator: BaseElectrodeRegistrator,
):
    model.compute_centroid()

    labeled_measured_electrodes = model.get_labeled_electrodes(
        [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
    )
    reference_electrodes = model.get_electrodes_by_modality(
        [ModalitiesMapping.REFERENCE]
    )

    if (status["electrodes_registered_to_reference"] is False) and len(
        labeled_measured_electrodes
    ) >= 3:
        electrode_registrator.register(
            source_electrodes=reference_electrodes,
            target_electrodes=labeled_measured_electrodes,
        )
        status["electrodes_registered_to_reference"] = True

        # self.display_unit_sphere()
        display_surface(views["labeling_reference"])


def undo_labeling(status: dict, electrode_registrator: BaseElectrodeRegistrator):
    if status["electrodes_registered_to_reference"]:
        electrode_registrator.undo()
        status["electrodes_registered_to_reference"] = False


def align_reference_electrodes_to_measured(
    model: CapModel,
    views: dict,
    status: dict,
    electrode_aligner: BaseElectrodeLabelingAligner,
):
    labeled_measured_electrodes = model.get_labeled_electrodes(
        [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
    )
    reference_electrodes = model.get_electrodes_by_modality(
        [ModalitiesMapping.REFERENCE]
    )

    measured_electrodes_matching_reference_labels = []
    for electrode in labeled_measured_electrodes:
        for reference_electrode in reference_electrodes:
            if electrode.label == reference_electrode.label:
                measured_electrodes_matching_reference_labels.append(electrode)

    assert len(
        set([e.label for e in measured_electrodes_matching_reference_labels])
    ) == len([e.label for e in measured_electrodes_matching_reference_labels])

    if (
        status["electrodes_registered_to_reference"]
        and len(measured_electrodes_matching_reference_labels) > 0
    ):
        electrode_aligner.set_source_electrodes(reference_electrodes)
        for electrode in measured_electrodes_matching_reference_labels:
            if electrode.label is not None:
                electrode_aligner.align(electrode)

    display_surface(views["labeling_reference"])


def autolabel_measured_electrodes():
    pass


def visualize_labeling_correspondence(
    model: CapModel, views: dict, slider: QSlider, slider_label: QLabel
):
    def f(x: float, k: float = 0.0088, n: float = 0.05):
        return k * x + n

    x = slider.value()
    correspondence_value = f(x)
    slider_label.setText(f"Value: {correspondence_value:.2f}")

    model.correspondence = compute_electrode_correspondence(
        labeled_reference_electrodes=model.get_unregistered_electrodes(
            [ModalitiesMapping.REFERENCE]
        ),
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
    model: CapModel,
    views: dict,
    status: dict,
    electrode_aligner: BaseElectrodeLabelingAligner,
):
    for entry in model.correspondence:
        # unlabeled_electrode = self.model.get_electrode_by_object_id(entry["electrode_id"])
        unlabeled_electrode = entry["electrode"]
        reference_electrode = model.get_electrode_by_label_and_modality(
            entry["suggested_label"], ModalitiesMapping.REFERENCE
        )
        if unlabeled_electrode is not None and reference_electrode is not None:
            unlabeled_electrode.label = reference_electrode.label

    align_reference_electrodes_to_measured(model, views, status, electrode_aligner)
