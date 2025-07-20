from ui.pyloc_main_window import Ui_ELK
from config.sizes import ElectrodeSizes
from view.surface_view import SurfaceView
from view.interactive_surface_view import InteractiveSurfaceView
from view.labeling_surface_view import LabelingSurfaceView
from processing_models.electrode_detector import BaseElectrodeDetector
from data_models.cap_model import CapModel
from data_models.head_models import HeadScan, MRIScan, UnitSphere

from config.mappings import ModalitiesMapping


def detect_electrodes(
    headmodel: HeadScan,
    electrode_detector: BaseElectrodeDetector,
    model: CapModel,
    ui: Ui_ELK | None,
):
    electrodes = electrode_detector.detect(headmodel.mesh)  # type: ignore
    for electrode in electrodes:
        model.insert_electrode(electrode)

    measured_electrodes = model.get_electrodes_by_modality(
        [ModalitiesMapping.HEADSCAN, ModalitiesMapping.MRI]
    )

    if ui:
        ui.measured_electrodes_label.setText(f"Measured: {len(measured_electrodes)}")
