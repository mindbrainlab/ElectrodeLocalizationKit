from PyQt6.QtWidgets import QFrame, QFileDialog
from ui.pyloc_main_window import Ui_ELK
from config.sizes import ElectrodeSizes
from view.labeling_surface_view import LabelingSurfaceView
from data_models.cap_model import CapModel
from data_models.head_models import UnitSphere


def load_locations(
    self: Ui_ELK,
    files: dict,
    views: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
):
    # remove existing reference electrodes
    reference_electrode = model.get_electrodes_by_modality(["reference"])
    if len(reference_electrode) > 0:
        for electrode in reference_electrode:
            electrode_id = model.get_electrode_id(electrode)
            if electrode_id is not None:
                model.remove_electrode_by_id(electrode_id)

    file_path, _ = QFileDialog.getOpenFileName(
        self,  # type: ignore
        "Open Locations File",
        "",
        "All Files (*);;CSV Files (*.csv)",
    )

    if file_path:
        reference_electrode = model.get_electrodes_by_modality(["reference"])
        if len(reference_electrode) > 0:
            for electrode in reference_electrode:
                electrode_id = model.get_electrode_id(electrode)
                if electrode_id is not None:
                    model.remove_electrode_by_id(electrode_id)

        files["locations"] = file_path
        model.read_electrodes_from_file(file_path)

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


def save_locations_to_file(model: CapModel):
    # file_path, _ = QFileDialog.getSaveFileName(
    #     self,
    #     "Save Locations File",
    #     "",
    #     "All Files (*);;CSV Files (*.csv)"
    #     )
    # if file_path:
    #     self.model.save_electrodes(file_path)

    model.save_electrodes_to_file("sample_data/measured_electrodes.ced")
