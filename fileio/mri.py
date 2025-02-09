from PyQt6.QtWidgets import QFrame
from ui.pyloc_main_window import Ui_ELK
from config.sizes import ElectrodeSizes
from view.interactive_surface_view import InteractiveSurfaceView
from data_models.cap_model import CapModel
from data_models.head_models import MRIScan


def load_mri(
    files: dict,
    views: dict,
    headmodels: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
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
