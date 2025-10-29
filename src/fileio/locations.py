from multiprocessing import Value
from PyQt6.QtWidgets import QFrame, QFileDialog
from config.sizes import ElectrodeSizes
from view.labeling_surface_view import LabelingSurfaceView
from data_models.cap_model import CapModel
from data_models.head_models import UnitSphere

import os
from pathlib import Path

from timing.timer import stage_timer

ENV = os.getenv("ELK_ENV", "production")


def load_locations(
    files: dict,
    views: dict,
    frames: list[tuple[str, QFrame]],
    model: CapModel,
):
    # remove existing reference electrodes
    # reference_electrode = model.get_electrodes_by_modality(["reference"])
    # if len(reference_electrode) > 0:
    #     for electrode in reference_electrode:
    #         electrode_id = model.get_electrode_id(electrode)
    #         if electrode_id is not None:
    #             model.remove_electrode_by_id(electrode_id)

    if ENV == "development":
        files["locations"] = "sample_data/electrode_locations.ced"
    else:
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Open Locations File",
            "",
            "CSV/TSV/CED Files (*.csv *.tsv *.ced);;All Files (*)",
        )
        files["locations"] = file_path

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


def save_locations_to_file(model: CapModel):
    file_path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Locations File",
        "",
        "CED Files (*.ced);;CSV Files (*.csv);;All Files (*)",
    )
    if file_path:
        stage_timer.log("FINAL STATE")
        stage_timer.save(filepath=Path(f"{Path(file_path).with_suffix('')}_timing.csv"))
        model.save_electrodes_to_file(file_path)
