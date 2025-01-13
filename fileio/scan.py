from PyQt6.QtWidgets import QFrame
from ui.pyloc_main_window import Ui_ELK
from config.sizes import ElectrodeSizes
from view.surface_view import SurfaceView
from view.interactive_surface_view import InteractiveSurfaceView
from processing_models.electrode_detector import BaseElectrodeDetector
from data_models.cap_model import CapModel
from data_models.head_models import HeadScan


# define slots (functions)
def load_surface(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    ui: Ui_ELK | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     None,
    #     "Open Surface File",
    #     "",
    #     "All Files (*);;STL Files (*.stl);;OBJ Files (*.obj)",
    # )
    # if file_path:
    #     files["scan"] = file_path

    files["scan"] = "sample_data/model_mesh.obj"

    headmodels["scan"] = HeadScan(files["scan"], files["texture"])

    for label, frame in frames:
        views[label] = create_surface_view(
            headmodels["scan"],
            frame,
            model,
        )

    if ui:
        ui.statusbar.showMessage("Loaded surface file.")


def load_texture(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    electrode_detector: BaseElectrodeDetector | None,
    ui: Ui_ELK | None,
):
    # file_path, _ = QFileDialog.getOpenFileName(
    #     self,
    #     "Open Texture File",
    #     "",
    #     "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
    #     )
    # if file_path:
    #     files["texture"] = file_path

    files["texture"] = "sample_data/model_mesh.jpg"

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
