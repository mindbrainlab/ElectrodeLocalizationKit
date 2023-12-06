from PyQt6.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QResizeEvent

from ui.pyloc_main_window import Ui_MainWindow

import vedo as vd

import sys
import numpy as np

from core.cap_model import CapModel
from core.head_models import HeadScan
from processing.electrode_detector import DogHoughElectrodeDetector
from ui.surface_view import SurfaceView
        
class StartQt6(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.label.setPixmap(QPixmap("ui/qt_designer/images/MainLogo.png"))

        # main data model
        self.model = CapModel()
        
        # table view
        self.ui.electrodes_table.setModel(self.model)

        # connect signals and slots
        self.ui.load_surface_button.clicked.connect(self.load_surface)
        self.ui.load_texture_button.clicked.connect(self.load_texture)
        self.ui.display_head_button.clicked.connect(self.display_surface)
        
        self.ui.display_dog_button.clicked.connect(self.display_dog)
        self.ui.kernel_size_spinbox.valueChanged.connect(self.display_dog)
        self.ui.sigma_spinbox.valueChanged.connect(self.display_dog)
        self.ui.diff_factor_spinbox.valueChanged.connect(self.display_dog)
        
        self.ui.display_hough_button.clicked.connect(self.display_hough)
        
        # spinboxes
        self.ui.param1_spinbox.valueChanged.connect(self.display_hough)
        self.ui.param2_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_dist_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_radius_spinbox.valueChanged.connect(self.display_hough)
        self.ui.max_radius_spinbox.valueChanged.connect(self.display_hough)
        
        self.ui.compute_electrodes_button.clicked.connect(
            self.detect_electrodes)
                
        self.ui.centralwidget.resizeEvent = self.on_resize       # type: ignore
        self.ui.centralwidget.closeEvent = self.on_close         # type: ignore
                
        self.image = None
        self.dog = None
        
        self.circles = None
        
        # temporary ===========================================================
        self.surface_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj'
        self.texture_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg'
        
        if self.surface_file and self.texture_file:
            self.head_scan = HeadScan(self.surface_file, self.texture_file)
            
        # ======================================================================
        
        self.surface_view = SurfaceView(self.ui.headmodel_frame,
                                        self.head_scan.mesh,
                                        self.head_scan.modality)
        self.surface_view.setModel(self.model)
        
        frame_size = self.ui.headmodel_frame.size()
        self.surface_view.resize_view(frame_size.width(), frame_size.height())
        
        self.dog_hough_detector = DogHoughElectrodeDetector(self.texture_file)
        
        # set status bar
        self.ui.statusbar.showMessage('Welcome!')
        
    # define slots (functions)
    def load_surface(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Surface File",
            "",
            "All Files (*);;STL Files (*.stl);;OBJ Files (*.obj)"
            )
        if file_path:
            self.surface_file = file_path

    def load_texture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Texture File",
            "",
            "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
            )
        if file_path:
            self.texture_file = file_path

    def display_surface(self):
        self.surface_view.setModel(self.model)
        
        frame_size = self.ui.headmodel_frame.size()
        self.surface_view.resize_view(frame_size.width(), frame_size.height())
        
        self.surface_view.show()

    def onMouseClick(self, evt):
        vd.printc("You have clicked your mouse button. Event info:\n",
                  evt,
                  c='y')

    def onKeypress(self, evt):
        vd.printc("You have pressed key:", evt.keypress, c='b')
        
    def get_vertex_from_pixels(self, pixels, mesh, image_size):
        # Helper function to get the vertex from the mesh that corresponds to
        # the pixel coordinates
        #
        # Written by: Aleksij Kraljic, October 29, 2023
        
        # extract the vertices from the mesh
        vertices = mesh.points()
        
        # extract the uv coordinates from the mesh
        uv = mesh.pointdata['material_0']
        
        # convert pixels to uv coordinates
        uv_image = [(pixels[0]+0.5)/image_size[0],
                    1-(pixels[1]+0.5)/image_size[1]]
        
        # find index of closest point in uv with uv_image
        uv_idx = np.argmin(np.linalg.norm(uv-uv_image, axis=1))
        
        return vertices[uv_idx]

    @pyqtSlot()
    def display_dog(self):
        self.dog = self.dog_hough_detector.get_difference_of_gaussians(
            ksize=self.ui.kernel_size_spinbox.value(),
            sigma=self.ui.sigma_spinbox.value(),
            F=self.ui.diff_factor_spinbox.value())
        
        self.dog_qimage = QImage(
            self.dog.data,
            self.dog.shape[1], self.dog.shape[0],
            QImage.Format.Format_Grayscale8).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.dog_qimage = self.dog_qimage.scaled(
            label_size.width(),label_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation)

        self.ui.photo_label.setPixmap(QPixmap.fromImage(self.dog_qimage))
        
    @pyqtSlot()
    def display_hough(self):
        self.hough = self.dog_hough_detector.get_hough_circles(
            param1=self.ui.param1_spinbox.value(),
            param2=self.ui.param2_spinbox.value(),
            min_distance_between_circles=self.ui.min_dist_spinbox.value(),
            min_radius=self.ui.min_radius_spinbox.value(),
            max_radius=self.ui.max_radius_spinbox.value())
        
        self.hough_qimage = QImage(
            self.hough.data,
            self.hough.shape[1], self.hough.shape[0],
            QImage.Format.Format_RGB888).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.hough_qimage = self.hough_qimage.scaled(
            label_size.width(), label_size.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation)

        self.ui.photo_label.setPixmap(QPixmap.fromImage(self.hough_qimage))
        
    @pyqtSlot()
    def detect_electrodes(self):
        self.electrodes = self.dog_hough_detector.detect_electrodes(
            self.head_scan.mesh)
        for electrode in self.electrodes:
            self.model.insert_electrode(electrode)

    def on_resize(self, event: QResizeEvent | None):
        frame_size = self.ui.headmodel_frame.size()
        
        if self.surface_view is not None:
            self.surface_view.resize_view(frame_size.width(),
                                          frame_size.height())
        
        if self.dog is not None:
             label_size = self.ui.texture_frame.size()
             self.dog_qimage = self.dog_qimage.scaled(
                 label_size.width(),
                 label_size.height(),
                 Qt.AspectRatioMode.KeepAspectRatio,
                 Qt.TransformationMode.FastTransformation)
             
             self.hough_qimage = self.hough_qimage.scaled(
                 label_size.width(),
                 label_size.height(),
                 Qt.AspectRatioMode.KeepAspectRatio,
                 Qt.TransformationMode.FastTransformation)

    def on_close(self):
        self.surface_view.close_vtk_widget()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = StartQt6()
    myapp.show()
    sys.exit(app.exec())