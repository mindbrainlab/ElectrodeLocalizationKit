import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt6.QtGui import QPixmap, QResizeEvent
from ui.pyloc_main_window import Ui_ELK

from data_models.cap_model import CapModel

from processing_models.electrode_detector import DogHoughElectrodeDetector
from processing_models.electrode_registrator import RigidElectrodeRegistrator
from processing_models.electrode_aligner import ElasticElectrodeAligner
from processing_models.surface_registrator import LandmarkSurfaceRegistrator

from ui.state_manager.state_machine import States, StateMachine
from ui.state_manager.states import initialize_fileio_states, initialize_processing_states
from ui.state_manager.transitions import (
    initialize_fileio_transitions,
    setup_master_state_reset,
    setup_mri_processing_no_locs_transitions,
    setup_mri_processing_transitions,
    setup_surface_processing_no_locs_transitions,
    setup_surface_processing_transitions,
    setup_surface_with_mri_processing_transitions,
    setup_surface_with_mri_processing_no_locs_transitions,
    setup_texture_processing_no_locs_transitions,
    setup_texture_processing_transitions,
    setup_texture_with_mri_processing_no_locs_transitions,
    setup_texture_with_mri_processing_transitions,
)

from ui.callbacks.refresh import refresh_views_on_resize
from ui.callbacks.connect.connect_fileio import connect_fileio_buttons
from ui.callbacks.connect.connect_texture import connect_texture_buttons
from ui.callbacks.connect.connect_configuration_boxes import connect_configuration_boxes
from ui.callbacks.connect.connect_sliders import connect_alpha_sliders
from ui.callbacks.connect.connect_model import connect_model
from ui.callbacks.connect.connect_labeling import connect_labeling_buttons
from ui.callbacks.connect.connect_state_transition_buttons import (
    connect_proceed_buttons,
    connect_back_buttons,
)
from ui.callbacks.connect.connect_resize import (
    connect_splitter_moved,
    connect_tab_changed,
)

from ui.callbacks.connect.connect_scan_mri_alignment import (
    connect_scan_mri_alignment_buttons,
    connect_display_secondary_mesh_checkbox,
)


class StartQt6(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ELK()
        self.ui.setupUi(self)
        self.ui.label.setPixmap(QPixmap("src/ui/qt_designer/images/MainLogo.png"))

        # main data containers
        self.set_data_containers()

        # main processing models
        self.model = CapModel()
        # detector for 2D image electrode detection
        self.electrode_detector = DogHoughElectrodeDetector()
        # registrator for headscan to MRI surface registration
        self.surface_registrator = LandmarkSurfaceRegistrator()
        # registrator for reference (manufacturer) and measured locations registration
        self.electrode_registrator = RigidElectrodeRegistrator()
        # aligner for reference electrodes to measured electrodes for automatic labeling
        self.electrode_aligner = ElasticElectrodeAligner()

        # connect callbacks
        connect_model(self)
        connect_fileio_buttons(self)
        connect_texture_buttons(self)
        connect_scan_mri_alignment_buttons(self)
        connect_display_secondary_mesh_checkbox(self)
        connect_configuration_boxes(self)
        connect_texture_buttons(self)
        connect_alpha_sliders(self)
        connect_tab_changed(self)
        connect_splitter_moved(self)
        connect_labeling_buttons(self)
        connect_proceed_buttons(self)
        connect_back_buttons(self)

        self.ui.tabWidget.setTabEnabled(0, True)
        self.ui.tabWidget.setTabEnabled(1, True)
        self.ui.tabWidget.setTabEnabled(2, True)
        self.ui.tabWidget.setTabEnabled(3, True)
        self.ui.tabWidget.setTabEnabled(4, True)

        self.state_machine = StateMachine(self.ui.statusbar)
        initialize_fileio_states(self)
        initialize_fileio_transitions(self)
        initialize_processing_states(self)
        setup_master_state_reset(self)
        setup_surface_processing_transitions(self)
        setup_surface_with_mri_processing_transitions(self)
        setup_surface_processing_no_locs_transitions(self)
        setup_mri_processing_transitions(self)
        setup_mri_processing_no_locs_transitions(self)
        setup_surface_with_mri_processing_no_locs_transitions(self)
        setup_texture_processing_transitions(self)
        setup_texture_processing_no_locs_transitions(self)
        setup_texture_with_mri_processing_transitions(self)
        setup_texture_with_mri_processing_no_locs_transitions(self)
        self.state_machine.set_initial_state(States.INITIAL.value)
        self.state_machine.state_changed.connect(self.ui.statusbar.showMessage)
        self.state_machine.start()

        # connect window events
        self.ui.centralwidget.resizeEvent = self.on_window_resize  # type: ignore
        self.ui.centralwidget.closeEvent = self.on_close  # type: ignore

    def set_data_containers(self):
        self.files = {
            "scan": None,
            "texture": None,
            "mri": None,
            "locations": None,
        }
        self.views = {
            "scan": None,
            "mri": None,
            "labeling_main": None,
            "labeling_reference": None,
        }
        self.headmodels = {
            "scan": None,
            "mri": None,
        }

        self.images = {"dog": None, "hough": None}

    def update_button_states(self, **kwargs):
        for button_name, enabled_state in kwargs.items():
            button = self.findChild(QPushButton, button_name)
            if button:
                print(f"Setting {button_name} to {enabled_state}")
                button.setEnabled(enabled_state)

    def update_tab_states(self, **kwargs):
        for tab_index, enabled_state in kwargs.items():
            print(f"Setting tab {tab_index} to {enabled_state}")
            self.ui.tabWidget.setTabEnabled(int(tab_index[1]), enabled_state)

    def update_texture_tab_states(self, **kwargs):
        for tab_index, enabled_state in kwargs.items():
            print(f"Setting texture tab {tab_index} to {enabled_state}")
            self.ui.tabWidget_texture.setTabEnabled(int(tab_index[1]), enabled_state)

    def switch_tab(self, tab_index):
        self.ui.tabWidget.setCurrentIndex(tab_index)

    def switch_texture_tab(self, tab_index):
        self.ui.tabWidget_texture.setCurrentIndex(tab_index)

    def on_window_resize(self, event: QResizeEvent):
        refresh_views_on_resize(
            self.views,
            [
                ("scan", self.ui.headmodel_frame),
                ("mri", self.ui.mri_frame),
                ("labeling_main", self.ui.labeling_main_frame),
                ("labeling_reference", self.ui.labeling_reference_frame),
            ],
        )

    def on_close(self):
        if self.views["scan"] is not None:
            self.views["scan"].close_vtk_widget()

        if self.views["mri"] is not None:
            self.views["mri"].close_vtk_widget()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = StartQt6()
    myapp.show()
    sys.exit(app.exec())
