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

from view.interactive_surface_view import InteractiveSurfaceView
from view.labeling_surface_view import LabelingSurfaceView

from config.mappings import ModalitiesMapping
from config.electrode_detector import DogParameters, HoughParameters
from config.sizes import ElectrodeSizes

from callbacks.display import display_surface


class StartQt6(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize variables
        self.surface_file = None
        self.texture_file = None
        self.mri_file = None
        self.surface_view = None
        self.mri_surface_view = None
        self.labeling_main_surface_view = None
        self.labeling_reference_surface_view = None
        self.image = None
        self.dog = None
        self.hough = None
        self.dog_hough_detector = None
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
        self.ui.load_surface_button.clicked.connect(self.load_surface)
        self.ui.load_texture_button.clicked.connect(self.load_texture)
        self.ui.load_mri_button.clicked.connect(self.load_mri)
        self.ui.load_locations_button.clicked.connect(self.load_locations)

        self.ui.export_locations_button.clicked.connect(self.save_locations_to_file)

        # display texture buttons slot connections
        self.ui.display_dog_button.clicked.connect(self.display_dog)
        self.ui.display_hough_button.clicked.connect(self.display_hough)

        # display surface buttons slot connections
        # self.ui.display_head_button.clicked.connect(self.display_surface)
        # self.ui.display_mri_button.clicked.connect(self.display_mri_surface)
        self.ui.display_head_button.clicked.connect(
            lambda: display_surface(self.surface_view)
        )
        self.ui.display_mri_button.clicked.connect(
            lambda: display_surface(self.mri_surface_view)
        )
        self.ui.label_display_button.clicked.connect(
            lambda: display_surface(self.labeling_main_surface_view)
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
        self.load_texture()
        self.load_surface()
        self.load_mri()
        self.load_locations()

        # set status bar
        self.ui.statusbar.showMessage("Welcome!")

    # define slots (functions)
    def load_surface(self):
        # file_path, _ = QFileDialog.getOpenFileName(
        #     self,
        #     "Open Surface File",
        #     "",
        #     "All Files (*);;STL Files (*.stl);;OBJ Files (*.obj)"
        #     )
        # if file_path:
        #     self.surface_file = file_path

        self.surface_file = "/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj"

        self.ui.statusbar.showMessage("Loaded surface file.")

        self.prepare_surface()
        self.ui.tabWidget.setTabEnabled(1, True)

    def load_texture(self):
        # file_path, _ = QFileDialog.getOpenFileName(
        #     self,
        #     "Open Texture File",
        #     "",
        #     "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        #     )
        # if file_path:
        #     self.texture_file = file_path

        self.texture_file = "/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg"
        self.dog_hough_detector = DogHoughElectrodeDetector(self.texture_file)

        self.ui.statusbar.showMessage("Loaded texture file.")

        self.prepare_surface()
        self.ui.tabWidget.setTabEnabled(2, True)

    def load_mri(self):
        # file_path, _ = QFileDialog.getOpenFileName(
        #     self,
        #     "Open MRI File",
        #     "",
        #     "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        #     )
        # if file_path:
        #     self.mri_file = file_path

        self.mri_file = "sample_data/bem_outer_skin_surface.gii"

        if self.mri_file:
            self.mri_scan = MRIScan(self.mri_file)

            self.mri_surface_view_config = {
                "sphere_size": ElectrodeSizes.MRI_ELECTRODE_SIZE,
                "draw_flagposts": False,
                "flagpost_height": ElectrodeSizes.MRI_FLAGPOST_HEIGHT,
                "flagpost_size": ElectrodeSizes.MRI_FLAGPOST_SIZE,
            }

            self.mri_surface_view = InteractiveSurfaceView(
                self.ui.mri_frame,
                self.mri_scan.mesh,
                [self.mri_scan.modality],
                self.mri_surface_view_config,
            )

            self.mri_surface_view.setModel(self.model)

            self.ui.statusbar.showMessage("Loaded MRI file.")
            self.ui.tabWidget.setTabEnabled(3, True)

    def load_locations(self):
        # file_path, _ = QFileDialog.getOpenFileName(
        #     self,
        #     "Open Locations File",
        #     "",
        #     "All Files (*);;CSV Files (*.csv)"
        #     )
        # if file_path:
        #     self.model.load_electrodes(file_path)

        reference_electrode = self.model.get_electrodes_by_modality(["reference"])
        if len(reference_electrode) > 0:
            for electrode in reference_electrode:
                electrode_id = self.model.get_electrode_id(electrode)
                if electrode_id is not None:
                    self.model.remove_electrode_by_id(electrode_id)

        self.model.read_electrodes_from_file(
            "sample_data/measured_reference_electrodes.ced"
        )

        self.unit_sphere_surface = UnitSphere()

        self.labeling_reference_surface_view_config = {
            "sphere_size": ElectrodeSizes.LABEL_ELECTRODE_SIZE,
            "draw_flagposts": False,
            "flagpost_height": ElectrodeSizes.LABEL_FLAGPOST_HEIGHT,
            "flagpost_size": ElectrodeSizes.LABEL_FLAGPOST_SIZE,
        }

        self.labeling_reference_surface_view = LabelingSurfaceView(
            self.ui.labeling_reference_frame,
            self.unit_sphere_surface.mesh,
            [self.unit_sphere_surface.modality],
            self.labeling_reference_surface_view_config,
        )

        self.labeling_reference_surface_view.setModel(self.model)

        self.ui.statusbar.showMessage("Loaded electrode locations.")
        self.ui.tabWidget.setTabEnabled(4, True)

    def save_locations_to_file(self):
        # file_path, _ = QFileDialog.getSaveFileName(
        #     self,
        #     "Save Locations File",
        #     "",
        #     "All Files (*);;CSV Files (*.csv)"
        #     )
        # if file_path:
        #     self.model.save_electrodes(file_path)

        self.model.save_electrodes_to_file("sample_data/measured_electrodes.ced")

        self.ui.statusbar.showMessage("Saved electrode locations.")

    def prepare_surface(self):
        if self.surface_file:
            self.head_scan = HeadScan(self.surface_file, self.texture_file)

            self.surface_view_config = {
                "sphere_size": ElectrodeSizes.HEADSCAN_ELECTRODE_SIZE,
                "draw_flagposts": False,
                "flagpost_height": ElectrodeSizes.HEADSCAN_FLAGPOST_HEIGHT,
                "flagpost_size": ElectrodeSizes.HEADSCAN_FLAGPOST_SIZE,
            }

            self.surface_view = InteractiveSurfaceView(
                self.ui.headmodel_frame,
                self.head_scan.mesh,  # type: ignore
                [self.head_scan.modality],
                self.surface_view_config,
            )

            # this is TEMPORARY, because it should also support MRI
            self.labeling_main_surface_view_config = {
                "sphere_size": ElectrodeSizes.HEADSCAN_ELECTRODE_SIZE,
                "draw_flagposts": False,
                "flagpost_height": ElectrodeSizes.HEADSCAN_FLAGPOST_HEIGHT,
                "flagpost_size": ElectrodeSizes.HEADSCAN_FLAGPOST_SIZE,
            }

            self.labeling_main_surface_view = InteractiveSurfaceView(
                self.ui.labeling_main_frame,
                self.head_scan.mesh,  # type: ignore
                [self.head_scan.modality],
                self.labeling_main_surface_view_config,
            )

            self.labeling_main_surface_view.setModel(self.model)

            self.surface_view.setModel(self.model)

            self.ui.statusbar.showMessage("Prepared headscan.")

    def refresh_views(self):
        t = self.ui.tabWidget.currentIndex()

        if t == 2:
            display_surface(self.surface_view)
        elif t == 3:
            display_surface(self.mri_surface_view)
        elif t == 4:
            display_surface(self.labeling_main_surface_view)
            display_surface(self.labeling_reference_surface_view)

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
        if self.mri_surface_view is not None:
            self.model.project_electrodes_to_mesh(
                self.mri_scan.mesh, ModalitiesMapping.HEADSCAN
            )
            self.mri_surface_view.show()
        # if self.head_scan is not None and self.mri_surface_view is not None:
        #     self.mri_surface_view.add_secondary_mesh(self.head_scan.mesh) # type: ignore

    def display_dog(self):
        if self.dog_hough_detector is not None:
            self.dog = self.dog_hough_detector.get_difference_of_gaussians(
                ksize=self.ui.kernel_size_spinbox.value(),
                sigma=self.ui.sigma_spinbox.value(),
                F=self.ui.diff_factor_spinbox.value(),
            )

            self.dog_qimage = QImage(
                self.dog.data,
                self.dog.shape[1],
                self.dog.shape[0],
                QImage.Format.Format_Grayscale8,
            ).rgbSwapped()

            label_size = self.ui.texture_frame.size()
            self.dog_qimage = self.dog_qimage.scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            self.ui.photo_label.setPixmap(QPixmap.fromImage(self.dog_qimage))

    def display_hough(self):
        if self.dog_hough_detector is not None:
            self.hough = self.dog_hough_detector.get_hough_circles(
                param1=self.ui.param1_spinbox.value(),
                param2=self.ui.param2_spinbox.value(),
                min_distance_between_circles=self.ui.min_dist_spinbox.value(),
                min_radius=self.ui.min_radius_spinbox.value(),
                max_radius=self.ui.max_radius_spinbox.value(),
            )

            self.hough_qimage = QImage(
                self.hough.data,
                self.hough.shape[1],
                self.hough.shape[0],
                QImage.Format.Format_RGB888,
            ).rgbSwapped()

            label_size = self.ui.texture_frame.size()
            self.hough_qimage = self.hough_qimage.scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

            self.ui.photo_label.setPixmap(QPixmap.fromImage(self.hough_qimage))

    def detect_electrodes(self):
        if self.dog_hough_detector is not None:
            self.electrodes = self.dog_hough_detector.detect(
                self.head_scan.mesh
            )  # type: ignore
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

        if self.surface_view is not None:
            self.surface_view.resize_view(
                scan_frame_size.width(), scan_frame_size.height()
            )

        if self.mri_surface_view is not None:
            self.mri_surface_view.resize_view(
                mri_frame_size.width(), mri_frame_size.height()
            )

        if self.labeling_main_surface_view is not None:
            self.labeling_main_surface_view.resize_view(
                label_main_frame_size.width(), label_main_frame_size.height()
            )

        if self.labeling_reference_surface_view is not None:
            self.labeling_reference_surface_view.resize_view(
                label_reference_frame_size.width(), label_reference_frame_size.height()
            )

        if self.dog is not None:
            label_size = self.ui.texture_frame.size()
            self.dog_qimage = self.dog_qimage.scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

        if self.hough is not None:
            label_size = self.ui.texture_frame.size()
            self.hough_qimage = self.hough_qimage.scaled(
                label_size.width(),
                label_size.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )

    def set_head_surf_alpha(self):
        if self.surface_view is not None:
            self.surface_view.update_surf_alpha(self.ui.head_alpha_slider.value() / 100)

    def set_mri_surf_alpha(self):
        if self.mri_surface_view is not None:
            self.mri_surface_view.update_surf_alpha(
                self.ui.mri_alpha_slider.value() / 100
            )

    def set_alignment_surf_alpha(self):
        if self.mri_surface_view is not None:
            self.mri_surface_view.update_secondary_surf_alpha(
                self.ui.mri_head_alpha_slider.value() / 100
            )

    def update_surf_config(self):
        if self.surface_view is not None:
            self.surface_view_config["sphere_size"] = (
                self.ui.sphere_size_spinbox.value()
            )
            self.surface_view_config["draw_flagposts"] = (
                self.ui.flagposts_checkbox.isChecked()
            )
            self.surface_view_config["flagpost_height"] = (
                self.ui.flagpost_height_spinbox.value()
            )
            self.surface_view_config["flagpost_size"] = (
                self.ui.flagpost_size_spinbox.value()
            )
            self.surface_view.update_config(self.surface_view_config)

        if self.labeling_main_surface_view is not None:
            self.labeling_main_surface_view_config["sphere_size"] = (
                self.ui.sphere_size_spinbox.value()
            )
            self.labeling_main_surface_view_config["draw_flagposts"] = (
                self.ui.flagposts_checkbox.isChecked()
            )
            self.labeling_main_surface_view_config["flagpost_height"] = (
                self.ui.flagpost_height_spinbox.value()
            )
            self.labeling_main_surface_view_config["flagpost_size"] = (
                self.ui.flagpost_size_spinbox.value()
            )
            self.labeling_main_surface_view.update_config(
                self.labeling_main_surface_view_config
            )

    def update_mri_config(self):
        if self.mri_surface_view is not None:
            self.mri_surface_view_config["sphere_size"] = (
                self.ui.mri_sphere_size_spinbox.value()
            )
            self.mri_surface_view_config["draw_flagposts"] = (
                self.ui.mri_flagposts_checkbox.isChecked()
            )
            self.mri_surface_view_config["flagpost_height"] = (
                self.ui.mri_flagpost_height_spinbox.value()
            )
            self.mri_surface_view_config["flagpost_size"] = (
                self.ui.mri_flagpost_size_spinbox.value()
            )
            self.mri_surface_view.update_config(self.mri_surface_view_config)

    def update_reference_labeling_config(self):
        if self.labeling_reference_surface_view is not None:
            self.labeling_reference_surface_view_config["sphere_size"] = (
                self.ui.label_sphere_size_spinbox.value()
            )
            self.labeling_reference_surface_view_config["draw_flagposts"] = (
                self.ui.label_flagposts_checkbox.isChecked()
            )
            self.labeling_reference_surface_view_config["flagpost_height"] = (
                self.ui.label_flagpost_height_spinbox.value()
            )
            self.labeling_reference_surface_view_config["flagpost_size"] = (
                self.ui.label_flagpost_size_spinbox.value()
            )
            self.labeling_reference_surface_view.update_config(
                self.labeling_reference_surface_view_config
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

        self.surface_registrator = LandmarkSurfaceRegistrator(
            source_mesh=self.head_scan.mesh,
            source_landmarks=scan_landmarks,
            target_landmarks=mri_landmarks,
        )

        # add the necessary checks

        transformation_matrix = self.head_scan.register_mesh(self.surface_registrator)
        if transformation_matrix is not None:
            self.model.transform_electrodes(
                ModalitiesMapping.HEADSCAN, transformation_matrix
            )

        self.ui.display_secondary_mesh_checkbox.setChecked(True)
        self.mri_surface_view.show()  # type: ignore

    def undo_scan2mri_transformation(self):
        inverse_transformation = self.head_scan.undo_registration(
            self.surface_registrator
        )
        # self.model.undo_transformation()
        # if inverse_transofrmation is not None:
        self.model.transform_electrodes(ModalitiesMapping.HEADSCAN, inverse_transformation)  # type: ignore
        self.mri_surface_view.reset_secondary_mesh()  # type: ignore
        self.ui.display_secondary_mesh_checkbox.setChecked(False)

    def display_secondary_mesh(self):
        if self.ui.display_secondary_mesh_checkbox.isChecked():
            self.mri_surface_view.add_secondary_mesh(self.head_scan.mesh)  # type: ignore
        else:
            self.mri_surface_view.reset_secondary_mesh()  # type: ignore
            self.mri_surface_view.show()  # type: ignore

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
            display_surface(self.labeling_reference_surface_view)

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

            display_surface(self.labeling_reference_surface_view)

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

        if self.labeling_reference_surface_view is not None:
            self.labeling_reference_surface_view.generate_correspondence_arrows(
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

            display_surface(self.labeling_reference_surface_view)
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
        if self.surface_view is not None:
            self.surface_view.close_vtk_widget()

        if self.mri_surface_view is not None:
            self.mri_surface_view.close_vtk_widget()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = StartQt6()
    myapp.show()
    sys.exit(app.exec())
