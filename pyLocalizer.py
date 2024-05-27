import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QPixmap, QResizeEvent
from ui.pyloc_main_window import Ui_MainWindow

from model.cap_model import CapModel

from processor.electrode_detector import DogHoughElectrodeDetector
from processor.electrode_registrator import RigidElectrodeRegistrator
from processor.electrode_aligner import ElasticElectrodeAligner
from processor.surface_registrator import LandmarkSurfaceRegistrator

from ui.callbacks.refresh_views import refresh_views_on_resize
from ui.callbacks.connect.connect_fileio import connect_fileio_buttons
from ui.callbacks.connect.connect_texture import connect_texture_buttons
from ui.callbacks.connect.connect_display import connect_display_surface_buttons
from ui.callbacks.connect.connect_configuration_boxes import connect_configuration_boxes
from ui.callbacks.connect.connect_sliders import connect_alpha_sliders
from ui.callbacks.connect.connect_model import connect_model
from ui.callbacks.connect.connect_labeling import connect_labeling_buttons
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
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.label.setPixmap(QPixmap("ui/qt_designer/images/MainLogo.png"))
        self.ui.statusbar.showMessage("Welcome!")

        # main data containers
        self.files = {"scan": None, "texture": None, "mri": None, "locations": None}
        self.views = {
            "scan": None,
            "mri": None,
            "labeling_main": None,
            "labeling_reference": None,
        }
        self.status = {
            "electrodes_registered_to_reference": False,
        }
        self.headmodels = {"scan": None, "mri": None}
        self.images = {"dog": None, "hough": None}

        # disable tabs -> this will be refactored in the future (UI state machine)
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tabWidget.setTabEnabled(2, False)
        self.ui.tabWidget.setTabEnabled(3, False)
        self.ui.tabWidget.setTabEnabled(4, False)

        # main processing models
        self.model = CapModel()
        self.electrode_detector = DogHoughElectrodeDetector()
        self.surface_registrator = LandmarkSurfaceRegistrator()
        self.electrode_registrator = RigidElectrodeRegistrator()
        self.electrode_aligner = ElasticElectrodeAligner()

        # connect callbacks
        connect_model(self)
        connect_fileio_buttons(self)
        connect_texture_buttons(self)
        connect_display_surface_buttons(self)
        connect_scan_mri_alignment_buttons(self)
        connect_display_secondary_mesh_checkbox(self)
        connect_configuration_boxes(self)
        connect_texture_buttons(self)
        connect_alpha_sliders(self)
        connect_tab_changed(self)
        connect_splitter_moved(self)
        connect_labeling_buttons(self)

        # connect window events
        self.ui.centralwidget.resizeEvent = self.on_window_resize  # type: ignore
        self.ui.centralwidget.closeEvent = self.on_close  # type: ignore

    def on_window_resize(self, event: QResizeEvent):
        refresh_views_on_resize(
            self.views,
            self.images,
            [
                ("scan", self.ui.headmodel_frame),
                ("mri", self.ui.mri_frame),
                ("labeling_main", self.ui.labeling_main_frame),
                ("labeling_reference", self.ui.labeling_reference_frame),
            ],
            self.ui.texture_frame,
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
