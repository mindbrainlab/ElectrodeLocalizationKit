from PyQt6.QtWidgets import QFrame, QFileDialog
from config.sizes import ElectrodeSizes
from view.surface_view import SurfaceView
from view.interactive_surface_view import InteractiveSurfaceView
from processing_models.electrode_detector import BaseElectrodeDetector
from data_models.cap_model import CapModel
from data_models.head_models import HeadScan
import os

ENV = os.getenv("ELK_ENV", "production")


# define slots (functions)
def load_surface(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
):
    if ENV == "development":
        files["scan"] = "sample_data/model_mesh.obj"
    else:
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Open Surface File", "", "OBJ/PLY Files (*.obj *.ply);;All Files (*)"
        )
        if file_path:
            files["scan"] = file_path

    headmodels["scan"] = HeadScan(files["scan"], files["texture"])

    for label, frame in frames:
        views[label] = create_surface_view(
            headmodels["scan"],
            frame,
            model,
        )


def load_texture(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
    electrode_detector: BaseElectrodeDetector | None,
):
    if ENV == "development":
        files["texture"] = "sample_data/model_mesh.jpg"
    else:
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Open Texture File",
            "",
            "Image Files (*.jpg *.jpeg *.bmp *.gif *.tiff)",
        )
        if file_path:
            files["texture"] = file_path

    if electrode_detector:
        electrode_detector.apply_texture(files["texture"])

    headmodels["scan"] = HeadScan(files["scan"], files["texture"])

    for label, frame in frames:
        views[label] = create_surface_view(
            headmodels["scan"],
            frame,
            model,
        )


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
