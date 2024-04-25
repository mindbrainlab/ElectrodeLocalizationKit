from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QPixmap, QResizeEvent

from ui.pyloc_main_window import Ui_MainWindow

import sys

from model.cap_model import CapModel

from processor.electrode_detector import DogHoughElectrodeDetector

from processor.electrode_registrator import RigidElectrodeRegistrator
from processor.electrode_aligner import (
    ElasticElectrodeAligner,
    compute_electrode_correspondence,
)

from config.mappings import ModalitiesMapping

from processor.surface_registrator import LandmarkSurfaceRegistrator


from ui.callbacks.display import display_surface
from ui.callbacks.config import update_view_config
from ui.callbacks.refresh_views import refresh_views_on_resize

from ui.callbacks.connect.connect_fileio import connect_fileio_buttons
from ui.callbacks.connect.connect_texture import connect_texture_buttons
from ui.callbacks.connect.connect_display import connect_display_surface_buttons
from ui.callbacks.connect.connect_configuration_boxes import connect_configuration_boxes
from ui.callbacks.connect.connect_sliders import connect_alpha_sliders
from ui.callbacks.connect.connect_model import connect_model
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

        # --- define the main dictionaries containing the core data models ----
        self.files = {"scan": None, "texture": None, "mri": None, "locations": None}

        self.views = {
            "scan": None,
            "mri": None,
            "labeling_main": None,
            "labeling_reference": None,
        }

        # self.frames = [
        #     ("scan", self.ui.headmodel_frame),
        #     ("mri", self.ui.mri_frame),
        #     ("labeling_main", self.ui.labeling_main_frame),
        #     ("labeling_reference", self.ui.labeling_reference_frame),
        #     ("texture", self.ui.texture_frame),
        # ]

        self.headmodels = {"scan": None, "mri": None}

        self.images = {"dog": None, "hough": None}

        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tabWidget.setTabEnabled(2, False)
        self.ui.tabWidget.setTabEnabled(3, False)
        self.ui.tabWidget.setTabEnabled(4, False)

        self.model = CapModel()
        self.electrode_detector = DogHoughElectrodeDetector()
        self.surface_registrator = LandmarkSurfaceRegistrator()

        self.ui.electrodes_table.setModel(self.model)
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
        self.ui.centralwidget.resizeEvent = self.on_window_resize  # type: ignore
        self.ui.centralwidget.closeEvent = self.on_close  # type: ignore

        self.electrodes_registered_to_reference = False
        self.correspondence = None

        self.ui.label_register_button.clicked.connect(
            self.register_reference_electrodes_to_measured
        )
        self.ui.label_align_button.clicked.connect(
            self.align_reference_electrodes_to_measured
        )
        self.ui.label_autolabel_button.clicked.connect(
            self.autolabel_measured_electrodes
        )
        self.ui.label_visualize_correspondence_button.clicked.connect(
            self.visualize_labeling_correspondence
        )

        self.ui.label_label_correspondence_button.clicked.connect(
            self.label_corresponding_electrodes
        )

        self.ui.correspondence_slider.valueChanged.connect(
            self.update_correspondence_value
        )
        self.ui.label_revert_button.clicked.connect(self.undo_labeling)

    def update_surf_config(self):
        if self.views["scan"] is not None:
            update_view_config(
                self.views["scan"],
                self.ui.sphere_size_spinbox.value(),
                self.ui.flagposts_checkbox.isChecked(),
                self.ui.flagpost_height_spinbox.value(),
                self.ui.flagpost_size_spinbox.value(),
            )

        if self.views["labeling_main"] is not None:
            update_view_config(
                self.views["labeling_main"],
                self.ui.sphere_size_spinbox.value(),
                self.ui.flagposts_checkbox.isChecked(),
                self.ui.flagpost_height_spinbox.value(),
                self.ui.flagpost_size_spinbox.value(),
            )

    def update_mri_config(self):
        if self.views["mri"] is not None:
            update_view_config(
                self.views["mri"],
                self.ui.mri_sphere_size_spinbox.value(),
                self.ui.mri_flagposts_checkbox.isChecked(),
                self.ui.mri_flagpost_height_spinbox.value(),
                self.ui.mri_flagpost_size_spinbox.value(),
            )

    def update_reference_labeling_config(self):
        if self.views["labeling_reference"] is not None:
            update_view_config(
                self.views["labeling_reference"],
                self.ui.label_sphere_size_spinbox.value(),
                self.ui.label_flagposts_checkbox.isChecked(),
                self.ui.label_flagpost_height_spinbox.value(),
                self.ui.label_flagpost_size_spinbox.value(),
            )

    def register_reference_electrodes_to_measured(self):
        self.model.compute_centroid()

        labeled_measured_electrodes = self.model.get_labeled_electrodes(
            [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
        )
        reference_electrodes = self.model.get_electrodes_by_modality(
            [ModalitiesMapping.REFERENCE]
        )

        if (not self.electrodes_registered_to_reference) and len(
            labeled_measured_electrodes
        ) >= 3:
            self.rigid_electrode_registrator = RigidElectrodeRegistrator(
                reference_electrodes
            )

            self.rigid_electrode_registrator.register(
                target_electrodes=labeled_measured_electrodes
            )
            self.electrodes_registered_to_reference = True

            # self.display_unit_sphere()
            display_surface(self.views["labeling_reference"])

    def undo_labeling(self):
        if self.electrodes_registered_to_reference:
            self.rigid_electrode_registrator.undo()
            self.electrodes_registered_to_reference = False

    def align_reference_electrodes_to_measured(self):
        labeled_measured_electrodes = self.model.get_labeled_electrodes(
            [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
        )
        reference_electrodes = self.model.get_electrodes_by_modality(
            [ModalitiesMapping.REFERENCE]
        )

        measured_electrodes_matching_reference_labels = []
        for electrode in labeled_measured_electrodes:
            for reference_electrode in reference_electrodes:
                if electrode.label == reference_electrode.label:
                    measured_electrodes_matching_reference_labels.append(electrode)

        assert len(
            set([e.label for e in measured_electrodes_matching_reference_labels])
        ) == len([e.label for e in measured_electrodes_matching_reference_labels])

        if (
            self.electrodes_registered_to_reference
            and len(measured_electrodes_matching_reference_labels) > 0
        ):
            electrode_aligner = ElasticElectrodeAligner(reference_electrodes)

            for electrode in measured_electrodes_matching_reference_labels:
                if electrode.label is not None:
                    electrode_aligner.align(electrode)

            display_surface(self.views["labeling_reference"])

    def autolabel_measured_electrodes(self):
        pass

    def visualize_labeling_correspondence(self):
        self.correspondence = compute_electrode_correspondence(
            labeled_reference_electrodes=self.model.get_unregistered_electrodes(
                [ModalitiesMapping.REFERENCE]
            ),
            unlabeled_measured_electrodes=self.model.get_unlabeled_electrodes(
                [ModalitiesMapping.MRI, ModalitiesMapping.HEADSCAN]
            ),
            factor_threshold=self.correspondence_value,
        )

        display_pairs = []
        for entry in self.correspondence:
            # unlabeled_electrode = self.model.get_electrode_by_object_id(entry["electrode_id"])
            unlabeled_electrode = entry["electrode"]
            reference_electrode = self.model.get_electrode_by_label_and_modality(
                entry["suggested_label"], ModalitiesMapping.REFERENCE
            )
            display_pairs.append((unlabeled_electrode, reference_electrode))

        if self.views["labeling_reference"] is not None:
            self.views["labeling_reference"].generate_correspondence_arrows(
                display_pairs
            )

    def label_corresponding_electrodes(self):
        if self.correspondence is not None:
            for entry in self.correspondence:
                # unlabeled_electrode = self.model.get_electrode_by_object_id(entry["electrode_id"])
                unlabeled_electrode = entry["electrode"]
                reference_electrode = self.model.get_electrode_by_label_and_modality(
                    entry["suggested_label"], ModalitiesMapping.REFERENCE
                )
                if unlabeled_electrode is not None and reference_electrode is not None:
                    unlabeled_electrode.label = reference_electrode.label

            display_surface(self.views["labeling_reference"])
            self.align_reference_electrodes_to_measured()

    def update_correspondence_value(self):
        def f(x: float, k: float = 0.0088, n: float = 0.05):
            return k * x + n

        x = self.ui.correspondence_slider.value()
        self.correspondence_value = f(x)
        self.ui.correspondence_slider_label.setText(
            f"Value: {self.correspondence_value:.2f}"
        )

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
