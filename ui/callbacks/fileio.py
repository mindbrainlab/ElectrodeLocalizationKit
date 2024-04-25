from PyQt6.QtWidgets import QFrame, QStatusBar, QTabWidget, QFileDialog

from ui.pyloc_main_window import Ui_MainWindow
from config.sizes import ElectrodeSizes
from view.surface_view import SurfaceView
from view.interactive_surface_view import InteractiveSurfaceView
from view.labeling_surface_view import LabelingSurfaceView
from processor.electrode_detector import BaseElectrodeDetector
from model.cap_model import CapModel
from model.head_models import HeadScan, MRIScan, UnitSphere


# define slots (functions)
def load_surface(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    ui: Ui_MainWindow | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     None,
    #     "Open Surface File",
    #     "",
    #     "All Files (*);;STL Files (*.stl);;OBJ Files (*.obj)",
    # )
    # if file_path:
    #     files["scan"] = file_path

    files["scan"] = (
        "/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj"
    )

    headmodels["scan"] = HeadScan(files["scan"], files["texture"])

    for label, frame in frames:
        views[label] = create_surface_view(
            headmodels["scan"],
            frame,
            model,
        )

    if ui:
        ui.statusbar.showMessage("Loaded surface file.")
        ui.tabWidget.setTabEnabled(1, True)


def load_texture(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    electrode_detector: BaseElectrodeDetector | None,
    ui: Ui_MainWindow | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     self,
    #     "Open Texture File",
    #     "",
    #     "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
    #     )
    # if file_path:
    #     files["texture"] = file_path

    files["texture"] = (
        "/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg"
    )

    if electrode_detector:
        electrode_detector.apply_texture(files["texture"])

    headmodels["scan"] = HeadScan(files["scan"], files["texture"])

    for label, frame in frames:
        views[label] = create_surface_view(
            headmodels["scan"],
            frame,
            model,
        )

    if ui:
        ui.statusbar.showMessage("Loaded texture file.")
        ui.tabWidget.setTabEnabled(2, True)


def load_mri(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    ui: Ui_MainWindow | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     self,
    #     "Open MRI File",
    #     "",
    #     "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
    #     )
    # if file_path:
    #     files["mri"] = file_path

    files["mri"] = "sample_data/bem_outer_skin_surface.gii"

    if files["mri"]:
        headmodels["mri"] = MRIScan(files["mri"])

        config = {
            "sphere_size": ElectrodeSizes.MRI_ELECTRODE_SIZE,
            "draw_flagposts": False,
            "flagpost_height": ElectrodeSizes.MRI_FLAGPOST_HEIGHT,
            "flagpost_size": ElectrodeSizes.MRI_FLAGPOST_SIZE,
        }

        for label, frame in frames:
            views[label] = InteractiveSurfaceView(
                frame,
                headmodels["mri"].mesh,
                [headmodels["mri"].modality],
                config,
                model,
            )

        if ui:
            ui.statusbar.showMessage("Loaded MRI file.")
            ui.tabWidget.setTabEnabled(3, True)


def load_locations(
    files: dict,
    views: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    ui: Ui_MainWindow | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     self,
    #     "Open Locations File",
    #     "",
    #     "All Files (*);;CSV Files (*.csv)"
    #     )
    # if file_path:
    #     reference_electrode = model.get_electrodes_by_modality(["reference"])
    #     if len(reference_electrode) > 0:
    #         for electrode in reference_electrode:
    #             electrode_id = model.get_electrode_id(electrode)
    #             if electrode_id is not None:
    #                 model.remove_electrode_by_id(electrode_id)
    #
    #     files["locations"] = file_path
    #     model.read_electrodes_from_file(file_path)

    # remove existing reference electrodes
    reference_electrode = model.get_electrodes_by_modality(["reference"])
    if len(reference_electrode) > 0:
        for electrode in reference_electrode:
            electrode_id = model.get_electrode_id(electrode)
            if electrode_id is not None:
                model.remove_electrode_by_id(electrode_id)

    # read new reference electrodes
    files["locations"] = "sample_data/measured_reference_electrodes.ced"
    model.read_electrodes_from_file(files["locations"])

    unit_sphere_mesh = UnitSphere()

    config = {
        "sphere_size": ElectrodeSizes.LABEL_ELECTRODE_SIZE,
        "draw_flagposts": False,
        "flagpost_height": ElectrodeSizes.LABEL_FLAGPOST_HEIGHT,
        "flagpost_size": ElectrodeSizes.LABEL_FLAGPOST_SIZE,
    }

    for label, frame in frames:
        views[label] = LabelingSurfaceView(
            frame,
            unit_sphere_mesh.mesh,
            [unit_sphere_mesh.modality],
            config,
            model,
        )

    if ui:
        ui.statusbar.showMessage("Loaded electrode locations.")
        ui.tabWidget.setTabEnabled(4, True)


def save_locations_to_file(model: CapModel, ui: Ui_MainWindow):
    # file_path, _ = QFileDialog.getSaveFileName(
    #     self,
    #     "Save Locations File",
    #     "",
    #     "All Files (*);;CSV Files (*.csv)"
    #     )
    # if file_path:
    #     self.model.save_electrodes(file_path)

    model.save_electrodes_to_file("sample_data/measured_electrodes.ced")

    if ui:
        ui.statusbar.showMessage("Saved electrode locations.")


def create_surface_view(
    head_scan: HeadScan,
    frame: QFrame,
    model: CapModel,
) -> SurfaceView | None:
    config = {
        "sphere_size": ElectrodeSizes.HEADSCAN_ELECTRODE_SIZE,
        "draw_flagposts": False,
        "flagpost_height": ElectrodeSizes.HEADSCAN_FLAGPOST_HEIGHT,
        "flagpost_size": ElectrodeSizes.HEADSCAN_FLAGPOST_SIZE,
    }

    surface_view = InteractiveSurfaceView(
        frame,
        head_scan.mesh,  # type: ignore
        [head_scan.modality],
        config,
        model,
    )

    return surface_view
