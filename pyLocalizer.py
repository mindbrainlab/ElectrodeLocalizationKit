from PyQt6.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent

from ui.pyloc_main_window import Ui_MainWindow

import sys

from model.cap_model import CapModel
from model.head_models import HeadScan, MRIScan, UnitSphere

from processor.electrode_detector import DogHoughElectrodeDetector
from processor.surface_registrator import LandmarkSurfaceRegistrator
from processor.electrode_registrator import RigidElectrodeRegistrator
from processor.electrode_aligner import (
    ElasticElectrodeAligner,
    compute_electrode_correspondence,
)

from view.surface_view import SurfaceView
from view.interactive_surface_view import InteractiveSurfaceView
from view.labeling_surface_view import LabelingSurfaceView

from config.mappings import ModalitiesMapping
from config.electrode_detector import DogParameters, HoughParameters
from config.sizes import ElectrodeSizes

from callbacks.display import display_surface, display_dog, display_hough
from callbacks.fileio import (
    load_surface,
    load_texture,
    load_mri,
    load_locations,
    save_locations_to_file,
)


class StartQt6(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize variables
        # self.surface_file = None
        # self.texture_file = None

        self.files = {"scan": None, "texture": None, "mri": None, "locations": None}
        self.views = {
            "scan": None,
            "mri": None,
            "labeling_main": None,
            "labeling_reference": None,
        }
        self.frames = [
            ("scan", self.ui.headmodel_frame),
            ("mri", self.ui.mri_frame),
            ("labeling_main", self.ui.labeling_main_frame),
            ("labeling_reference", self.ui.labeling_reference_frame),
        ]
        self.headmodels = {"scan": None, "mri": None}

        self.images = {"dog": None, "hough": None}

        # self.mri_file = None
        # self.surface_view = None
        # self.mri_surface_view = None
        # self.labeling_main_surface_view = None
        # self.labeling_reference_surface_view = None
        self.image = None
        self.dog = None
        self.hough = None
        # self.dog_hough_detector = None
        self.circles = None
        self.electrodes_registered_to_reference = False
        self.correspondence = None

        self.ui.label.setPixmap(QPixmap("ui/qt_designer/images/MainLogo.png"))

        # main data model
        self.model = CapModel()

        self.model.dataChanged.connect(self.refresh_count_indicators)
        self.model.rowsInserted.connect(self.refresh_count_indicators)
        self.model.rowsRemoved.connect(self.refresh_count_indicators)

        # disable tabs
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tabWidget.setTabEnabled(2, False)
        self.ui.tabWidget.setTabEnabled(3, False)
        self.ui.tabWidget.setTabEnabled(4, False)

        # table view
        self.ui.electrodes_table.setModel(self.model)

        # load buttons slot connections
        self.ui.load_surface_button.clicked.connect(
            lambda: load_surface(
                self.files,
                self.views,
                self.headmodels,
                [
                    ("scan", self.ui.headmodel_frame),
                    ("labeling_main", self.ui.labeling_main_frame),
                ],
                self.model,
                self.ui,
            )
        )

        self.electrode_detector = DogHoughElectrodeDetector()
        self.ui.load_texture_button.clicked.connect(
            lambda: load_texture(
                self.files,
                self.views,
                self.headmodels,
                [
                    ("scan", self.ui.headmodel_frame),
                    ("labeling_main", self.ui.labeling_main_frame),
                ],
                self.model,
                self.electrode_detector,
                self.ui,
            )
        )
        self.ui.load_mri_button.clicked.connect(
            lambda: load_mri(
                self.files,
                self.views,
                self.headmodels,
                [("mri", self.ui.mri_frame)],
                self.model,
                self.ui,
            )
        )
        self.ui.load_locations_button.clicked.connect(
            lambda: load_locations(
                self.files,
                self.views,
                [("labeling_reference", self.ui.labeling_reference_frame)],
                self.model,
                self.ui,
            )
        )

        self.ui.export_locations_button.clicked.connect(
            lambda: save_locations_to_file(self.model, self.ui)
        )

        # display texture buttons slot connections
        self.ui.display_dog_button.clicked.connect(self.display_dog)

        self.ui.display_hough_button.clicked.connect(self.display_hough)

        # display surface buttons slot connections
        self.ui.display_head_button.clicked.connect(
            lambda: display_surface(self.views["scan"])
        )
        self.ui.display_mri_button.clicked.connect(
            lambda: display_surface(self.views["mri"])
        )
        self.ui.label_display_button.clicked.connect(
            lambda: display_surface(self.views["labeling_main"])
        )

        # surface to mri alignment buttons slot connections
        self.ui.align_scan_button.clicked.connect(self.align_scan_to_mri)
        self.ui.project_electrodes_button.clicked.connect(
            self.project_electrodes_to_mri
        )
        self.ui.revert_alignment_button.clicked.connect(
            self.undo_scan2mri_transformation
        )

        # texture detect electrodes button slot connection
        self.ui.compute_electrodes_button.clicked.connect(self.detect_electrodes)

        # texture DoG spinbox slot connections
        self.ui.kernel_size_spinbox.valueChanged.connect(self.display_dog)
        self.ui.sigma_spinbox.valueChanged.connect(self.display_dog)
        self.ui.diff_factor_spinbox.valueChanged.connect(self.display_dog)

        # texture Hough spinbox slot connections
        self.ui.param1_spinbox.valueChanged.connect(self.display_hough)
        self.ui.param2_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_dist_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_radius_spinbox.valueChanged.connect(self.display_hough)
        self.ui.max_radius_spinbox.valueChanged.connect(self.display_hough)

        # surface configuration slot connections
        self.ui.sphere_size_spinbox.valueChanged.connect(self.update_surf_config)
        self.ui.flagposts_checkbox.stateChanged.connect(self.update_surf_config)
        self.ui.flagpost_height_spinbox.valueChanged.connect(self.update_surf_config)
        self.ui.flagpost_size_spinbox.valueChanged.connect(self.update_surf_config)

        # mri configuration slot connections
        self.ui.mri_sphere_size_spinbox.valueChanged.connect(self.update_mri_config)
        self.ui.mri_flagposts_checkbox.stateChanged.connect(self.update_mri_config)
        self.ui.mri_flagpost_height_spinbox.valueChanged.connect(self.update_mri_config)
        self.ui.mri_flagpost_size_spinbox.valueChanged.connect(self.update_mri_config)

        # label configuration slot connections
        self.ui.label_sphere_size_spinbox.valueChanged.connect(
            self.update_reference_labeling_config
        )
        self.ui.label_flagposts_checkbox.stateChanged.connect(
            self.update_reference_labeling_config
        )
        self.ui.label_flagpost_height_spinbox.valueChanged.connect(
            self.update_reference_labeling_config
        )
        self.ui.label_flagpost_size_spinbox.valueChanged.connect(
            self.update_reference_labeling_config
        )

        self.ui.splitter.splitterMoved.connect(self.on_resize)

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

        # alpha slider slot connections
        self.ui.head_alpha_slider.valueChanged.connect(self.set_head_surf_alpha)
        self.ui.mri_alpha_slider.valueChanged.connect(self.set_mri_surf_alpha)
        self.ui.mri_head_alpha_slider.valueChanged.connect(
            self.set_alignment_surf_alpha
        )

        self.ui.display_secondary_mesh_checkbox.stateChanged.connect(
            self.display_secondary_mesh
        )

        self.ui.tabWidget.currentChanged.connect(self.refresh_views)

        # resize and close event slot connections
        self.ui.centralwidget.resizeEvent = self.on_resize  # type: ignore
        self.ui.centralwidget.closeEvent = self.on_close  # type: ignore

        # texture DoG spinbox default values
        self.ui.kernel_size_spinbox.setValue(DogParameters.KSIZE)
        self.ui.sigma_spinbox.setValue(DogParameters.SIGMA)
        self.ui.diff_factor_spinbox.setValue(DogParameters.FACTOR)

        # texture Hough spinbox default values
        self.ui.param1_spinbox.setValue(HoughParameters.PARAM1)
        self.ui.param2_spinbox.setValue(HoughParameters.PARAM2)
        self.ui.min_dist_spinbox.setValue(HoughParameters.MIN_DISTANCE)
        self.ui.min_radius_spinbox.setValue(HoughParameters.MIN_RADIUS)
        self.ui.max_radius_spinbox.setValue(HoughParameters.MAX_RADIUS)

        # electrode size spinbox default values
        self.ui.sphere_size_spinbox.setValue(ElectrodeSizes.HEADSCAN_ELECTRODE_SIZE)
        self.ui.flagpost_size_spinbox.setValue(ElectrodeSizes.HEADSCAN_FLAGPOST_SIZE)
        self.ui.flagpost_height_spinbox.setValue(
            ElectrodeSizes.HEADSCAN_FLAGPOST_HEIGHT
        )

        # mri electrode size spinbox default values
        self.ui.mri_sphere_size_spinbox.setValue(ElectrodeSizes.MRI_ELECTRODE_SIZE)
        self.ui.mri_flagpost_size_spinbox.setValue(ElectrodeSizes.MRI_FLAGPOST_SIZE)
        self.ui.mri_flagpost_height_spinbox.setValue(ElectrodeSizes.MRI_FLAGPOST_HEIGHT)

        # label electrode size spinbox default values
        self.ui.label_sphere_size_spinbox.setValue(ElectrodeSizes.LABEL_ELECTRODE_SIZE)
        self.ui.label_flagpost_size_spinbox.setValue(ElectrodeSizes.LABEL_FLAGPOST_SIZE)
        self.ui.label_flagpost_height_spinbox.setValue(
            ElectrodeSizes.LABEL_FLAGPOST_HEIGHT
        )

        # temporary calls to avoid loading files during development
        # self.load_texture()
        # self.load_surface()
        # self.load_mri()
        # self.load_locations()

        # set status bar
        self.ui.statusbar.showMessage("Welcome!")

    def refresh_views(self):
        t = self.ui.tabWidget.currentIndex()

        if t == 2:
            display_surface(self.views["scan"])
        elif t == 3:
            display_surface(self.views["mri"])
        elif t == 4:
            display_surface(self.views["labeling_main"])
            display_surface(self.views["labeling_reference"])

    def refresh_count_indicators(self):
        measured_electrodes = self.model.get_electrodes_by_modality(
            [ModalitiesMapping.HEADSCAN, ModalitiesMapping.MRI]
        )
        self.ui.measured_electrodes_label.setText(
            f"Measured electrodes: {len(measured_electrodes)}"
        )

        labeled_electrodes = []
        for electrode in measured_electrodes:
            if not (
                electrode.label is None
                or electrode.label == ""
                or electrode.label == "None"
            ):
                labeled_electrodes.append(electrode)

        self.ui.labeled_electrodes_label.setText(
            f"Labeled electrodes: {len(labeled_electrodes)}"
        )

        reference_electrode = self.model.get_electrodes_by_modality(["reference"])
        self.ui.reference_electrodes_label.setText(
            f"Reference electrodes: {len(reference_electrode)}"
        )

    def project_electrodes_to_mri(self):
        if self.headmodels["mri"] is not None:
            self.model.project_electrodes_to_mesh(
                self.headmodels["mri"].mesh, ModalitiesMapping.HEADSCAN
            )
            self.headmodels["mri"].show()
        # if self.head_scan is not None and self.views["mri"] is not None:
        #     self.views["mri"].add_secondary_mesh(self.head_scan.mesh) # type: ignore

    def display_dog(self):
        if self.files["texture"] is not None:
            display_dog(
                self.images,
                self.ui.texture_frame,
                self.ui.photo_label,
                self.electrode_detector,
                self.ui.kernel_size_spinbox.value(),
                self.ui.sigma_spinbox.value(),
                self.ui.diff_factor_spinbox.value(),
            )

    def display_hough(self):
        if self.files["texture"] is not None:
            display_hough(
                self.images,
                self.ui.texture_frame,
                self.ui.photo_label,
                self.electrode_detector,
                self.ui.param1_spinbox.value(),
                self.ui.param2_spinbox.value(),
                self.ui.min_dist_spinbox.value(),
                self.ui.min_radius_spinbox.value(),
                self.ui.max_radius_spinbox.value(),
            )

    def detect_electrodes(self):
        if self.electrode_detector is not None and self.headmodels["scan"] is not None:
            self.electrodes = self.electrode_detector.detect(
                self.headmodels["scan"].mesh
            )
            for electrode in self.electrodes:
                self.model.insert_electrode(electrode)

            measured_electrodes = self.model.get_electrodes_by_modality(
                [ModalitiesMapping.HEADSCAN, ModalitiesMapping.MRI]
            )
            self.ui.measured_electrodes_label.setText(
                f"Measured electrodes: {len(measured_electrodes)}"
            )

    def on_resize(self, event: QResizeEvent | None):
        scan_frame_size = self.ui.headmodel_frame.size()
        mri_frame_size = self.ui.mri_frame.size()
        label_main_frame_size = self.ui.labeling_main_frame.size()
        label_reference_frame_size = self.ui.labeling_reference_frame.size()

        if self.views["scan"] is not None:
            self.views["scan"].resize_view(
                scan_frame_size.width(), scan_frame_size.height()
            )

        if self.views["mri"] is not None:
            self.views["mri"].resize_view(
                mri_frame_size.width(), mri_frame_size.height()
            )

        if self.views["labeling_main"] is not None:
            self.views["labeling_main"].resize_view(
                label_main_frame_size.width(), label_main_frame_size.height()
            )

        if self.views["labeling_reference"] is not None:
            self.views["labeling_reference"].resize_view(
                label_reference_frame_size.width(), label_reference_frame_size.height()
            )

        if self.images["dog"] is not None:
            label_size = self.ui.texture_frame.size()
            self.images["dog"] = self.images["dog"].scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

        if self.images["hough"] is not None:
            label_size = self.ui.texture_frame.size()
            self.images["hough"] = self.images["hough"].scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

    def set_head_surf_alpha(self):
        if self.views["scan"] is not None:
            self.views["scan"].update_surf_alpha(
                self.ui.head_alpha_slider.value() / 100
            )

    def set_mri_surf_alpha(self):
        if self.views["mri"] is not None:
            self.views["mri"].update_surf_alpha(self.ui.mri_alpha_slider.value() / 100)

    def set_alignment_surf_alpha(self):
        if self.views["mri"] is not None:
            self.views["mri"].update_secondary_surf_alpha(
                self.ui.mri_head_alpha_slider.value() / 100
            )

    def _update_view_config(
        self,
        view: SurfaceView,
        sphere_size: float,
        draw_flagposts: bool,
        flagpost_height: float,
        flagpost_size: float,
    ):
        config = {
            "sphere_size": sphere_size,
            "draw_flagposts": draw_flagposts,
            "flagpost_height": flagpost_height,
            "flagpost_size": flagpost_size,
        }
        view.update_config(config)

    def update_surf_config(self):
        if self.views["scan"] is not None:
            self._update_view_config(
                self.views["scan"],
                self.ui.sphere_size_spinbox.value(),
                self.ui.flagposts_checkbox.isChecked(),
                self.ui.flagpost_height_spinbox.value(),
                self.ui.flagpost_size_spinbox.value(),
            )

        if self.views["labeling_main"] is not None:
            self._update_view_config(
                self.views["labeling_main"],
                self.ui.sphere_size_spinbox.value(),
                self.ui.flagposts_checkbox.isChecked(),
                self.ui.flagpost_height_spinbox.value(),
                self.ui.flagpost_size_spinbox.value(),
            )

    def update_mri_config(self):
        if self.views["mri"] is not None:
            self._update_view_config(
                self.views["mri"],
                self.ui.mri_sphere_size_spinbox.value(),
                self.ui.mri_flagposts_checkbox.isChecked(),
                self.ui.mri_flagpost_height_spinbox.value(),
                self.ui.mri_flagpost_size_spinbox.value(),
            )

    def update_reference_labeling_config(self):
        if self.views["labeling_reference"] is not None:
            self._update_view_config(
                self.views["labeling_reference"],
                self.ui.label_sphere_size_spinbox.value(),
                self.ui.label_flagposts_checkbox.isChecked(),
                self.ui.label_flagpost_height_spinbox.value(),
                self.ui.label_flagpost_size_spinbox.value(),
            )

    def align_scan_to_mri(self):
        scan_labeled_electrodes = self.model.get_labeled_electrodes(
            [ModalitiesMapping.HEADSCAN]
        )
        mri_labeled_electrodes = self.model.get_labeled_electrodes(
            [ModalitiesMapping.MRI]
        )

        scan_landmarks = []
        mri_landmarks = []
        for electrode_i in scan_labeled_electrodes:
            for electrode_j in mri_labeled_electrodes:
                if electrode_i.label == electrode_j.label:
                    scan_landmarks.append(electrode_i.coordinates)
                    mri_landmarks.append(electrode_j.coordinates)

        if self.headmodels["scan"] is not None:
            self.surface_registrator = LandmarkSurfaceRegistrator(
                source_mesh=self.headmodels["scan"].mesh,
                source_landmarks=scan_landmarks,
                target_landmarks=mri_landmarks,
            )

        # add the necessary checks

        transformation_matrix = self.headmodels["scan"].register_mesh(self.surface_registrator)  # type: ignore
        if transformation_matrix is not None:
            self.model.transform_electrodes(
                ModalitiesMapping.HEADSCAN, transformation_matrix
            )

        self.ui.display_secondary_mesh_checkbox.setChecked(True)
        self.views["mri"].show()  # type: ignore

    def undo_scan2mri_transformation(self):
        inverse_transformation = self.headmodels["scan"].undo_registration(  # type: ignore
            self.surface_registrator
        )
        # self.model.undo_transformation()
        # if inverse_transofrmation is not None:
        self.model.transform_electrodes(ModalitiesMapping.HEADSCAN, inverse_transformation)  # type: ignore
        self.views["mri"].reset_secondary_mesh()  # type: ignore
        self.ui.display_secondary_mesh_checkbox.setChecked(False)

    def display_secondary_mesh(self):
        if self.ui.display_secondary_mesh_checkbox.isChecked():
            self.views["mri"].add_secondary_mesh(self.head_scan.mesh)  # type: ignore
        else:
            self.views["mri"].reset_secondary_mesh()  # type: ignore
            self.views["mri"].show()  # type: ignore

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
