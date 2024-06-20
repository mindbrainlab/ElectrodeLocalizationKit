from ui.pyloc_main_window import Ui_ELK

from PyQt6.QtWidgets import QCheckBox

from config.mappings import ModalitiesMapping
from processor.surface_registrator import LandmarkSurfaceRegistrator

from model.cap_model import CapModel


def align_scan_to_mri(
    views: dict,
    headmodels: dict,
    model: CapModel,
    surface_registrator: LandmarkSurfaceRegistrator,
    ui: Ui_ELK | None,
):
    scan_labeled_electrodes = model.get_labeled_electrodes([ModalitiesMapping.HEADSCAN])
    mri_labeled_electrodes = model.get_labeled_electrodes([ModalitiesMapping.MRI])

    scan_landmarks = []
    mri_landmarks = []
    for electrode_i in scan_labeled_electrodes:
        for electrode_j in mri_labeled_electrodes:
            if electrode_i.label == electrode_j.label:
                scan_landmarks.append(electrode_i.coordinates)
                mri_landmarks.append(electrode_j.coordinates)

    surface_registrator.set_mesh(headmodels["scan"].mesh)
    surface_registrator.set_landmarks(scan_landmarks, mri_landmarks)

    transformation_matrix = headmodels["scan"].register_mesh(surface_registrator)  # type: ignore
    if transformation_matrix is not None:
        model.transform_electrodes(ModalitiesMapping.HEADSCAN, transformation_matrix)

    if ui:
        ui.display_secondary_mesh_checkbox.setChecked(True)
    views["mri"].show()


def undo_scan2mri_transformation(
    views: dict,
    headmodels: dict,
    model: CapModel,
    surface_registrator: LandmarkSurfaceRegistrator,
    ui: Ui_ELK | None,
):
    inverse_transformation = headmodels["scan"].undo_registration(surface_registrator)
    model.transform_electrodes(ModalitiesMapping.HEADSCAN, inverse_transformation)
    views["mri"].reset_secondary_mesh()

    if ui:
        ui.display_secondary_mesh_checkbox.setChecked(False)


def project_electrodes_to_mri(headmodels: dict, model: CapModel):
    model.project_electrodes_to_mesh(headmodels["mri"].mesh, ModalitiesMapping.HEADSCAN)
    # headmodels["mri"].show()


def display_secondary_mesh(views: dict, headmodels: dict, checkbox: QCheckBox):
    if checkbox.isChecked():
        views["mri"].add_secondary_mesh(headmodels["scan"].mesh)  # type: ignore
    else:
        views["mri"].reset_secondary_mesh()  # type: ignore
        views["mri"].show()  # type: ignore
