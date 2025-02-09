from fileio import mri
from ui.pyloc_main_window import Ui_ELK

from PyQt6.QtWidgets import QCheckBox

from config.mappings import ModalitiesMapping
from processing_models.surface_registrator import LandmarkSurfaceRegistrator

from data_models.cap_model import CapModel
from utils.warnings import throw_fiducials_warning


def align_scan_to_mri(
    views: dict,
    headmodels: dict,
    model: CapModel,
    surface_registrator: LandmarkSurfaceRegistrator,
    ui: Ui_ELK | None,
):
    scan_fiducials = model.get_fiducials(ModalitiesMapping.HEADSCAN)
    mri_fiducials = model.get_fiducials(ModalitiesMapping.MRI)

    scan_fiducials_labels = [fid.label for fid in scan_fiducials]
    mri_fiducials_labels = [fid.label for fid in mri_fiducials]

    fiducials_labels_intersection = set(scan_fiducials_labels).intersection(
        set(mri_fiducials_labels)
    )

    if len(fiducials_labels_intersection) < 3:
        throw_fiducials_warning()
        return

    scan_landmarks = []
    mri_landmarks = []
    for scan_fiducial_label in scan_fiducials_labels:
        scan_landmarks.append(
            [fid.coordinates for fid in scan_fiducials if fid.label == scan_fiducial_label][0]
        )
        mri_landmarks.append(
            [fid.coordinates for fid in mri_fiducials if fid.label == scan_fiducial_label][0]
        )

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
