from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import QTabWidget, QLabel, QFrame
from PyQt6.QtCore import Qt
from ui.callbacks.display import display_surface
from config.mappings import ModalitiesMapping

from data_models.cap_model import CapModel


def refresh_views_on_tab_change(tab_widget: QTabWidget, views: dict):
    t = tab_widget.currentIndex()

    if t == 2:
        display_surface(views["scan"])
    elif t == 3:
        display_surface(views["mri"])
    elif t == 4:
        display_surface(views["labeling_main"])
        display_surface(views["labeling_reference"])


def refresh_count_indicators(
    model: CapModel,
    measured_electrodes_label: QLabel,
    labeled_electrodes_label: QLabel,
    reference_electrodes_label: QLabel,
):
    measured_electrodes = model.get_electrodes_by_modality(
        [ModalitiesMapping.HEADSCAN, ModalitiesMapping.MRI]
    )

    measured_electrodes_label.setText(f"Measured electrodes: {len(measured_electrodes)}")

    labeled_electrodes = []
    for electrode in measured_electrodes:
        if not (electrode.label is None or electrode.label == "" or electrode.label == "None"):
            labeled_electrodes.append(electrode)

    labeled_electrodes_label.setText(f"Labeled electrodes: {len(labeled_electrodes)}")

    reference_electrode = model.get_electrodes_by_modality(["reference"])
    reference_electrodes_label.setText(f"Reference electrodes: {len(reference_electrode)}")


# def refresh_views_on_resize(self, event: QResizeEvent | None):
def refresh_views_on_resize(
    views: dict,
    images: dict,
    surface_frames: list[tuple[str, QFrame]],
    texture_frame: QFrame,
):
    for label, frame in surface_frames:
        if views[label] is not None:
            views[label].resize_view(frame.size().width(), frame.size().height())

    if images["dog"] is not None:
        label_size = texture_frame.size()
        images["dog"] = images["dog"].scaled(
            label_size.width(),
            label_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

    if images["hough"] is not None:
        label_size = texture_frame.size()
        images["hough"] = images["hough"].scaled(
            label_size.width(),
            label_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
