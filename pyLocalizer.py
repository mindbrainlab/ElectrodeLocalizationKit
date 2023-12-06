from PyQt6.QtWidgets import QMainWindow, QFileDialog, QApplication
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap

from ui.pyloc_main_window import Ui_MainWindow

import vedo as vd
from icecream import ic

import sys
from time import sleep
import numpy as np
import pandas as pd

import cv2 as cv

from core.cap_model import CapModel
from core.electrode import Electrode

from core.head_models import HeadScan

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
        
        self.ui.compute_electrodes_button.clicked.connect(self.compute_electrodes)
                
        self.ui.centralwidget.resizeEvent = self.onResize
                
        self.image = None
        self.dog = None
        
        self.circles = None
        
        # temporary ===========================================================
        self.surface_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj'
        self.texture_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg'
        
        if self.surface_file and self.texture_file:
            self.head_scan = HeadScan(self.surface_file, self.texture_file)
            
        # ======================================================================
        
        self.surface_view = SurfaceView(self.ui.headmodel_frame, self.head_scan.mesh, self.head_scan.modality)
        self.surface_view.setModel(self.model)
        
        # set status bar
        self.ui.statusbar.showMessage('Welcome!')
        
    # define slots (functions)
    def load_surface(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Surface File", "", "All Files (*);;STL Files (*.stl);;OBJ Files (*.obj)")
        if file_path:
            self.surface_file = file_path
            ic(self.surface_file)

    def load_texture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Texture File", "", "All Files (*);;Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)")
        if file_path:
            self.texture_file = file_path
            ic(self.texture_file)

    def display_surface(self):
        # self.surface_view.mesh = self.head_scan.mesh
        # self.surface_view.modality = self.head_scan.modality
        
        frame_size = self.ui.headmodel_frame.size()
        self.surface_view.resize_view(frame_size.width(), frame_size.height())
        
        self.surface_view.show()

    def onMouseClick(self, evt):
        vd.printc("You have clicked your mouse button. Event info:\n", evt, c='y')

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
        uv_image = [(pixels[0]+0.5)/image_size[0], 1-(pixels[1]+0.5)/image_size[1]]
        
        # find index of closest point in uv with uv_image
        uv_idx = np.argmin(np.linalg.norm(uv-uv_image, axis=1))
        
        return vertices[uv_idx]

    @pyqtSlot()
    def display_dog(self):
        if self.image is None:
            self.image = cv.imread(self.texture_file)
            self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
            self.dog = QImage(self.dog.data, self.dog.shape[1], self.dog.shape[0], QImage.Format.Format_Grayscale8).rgbSwapped()
        else:
            self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
            self.dog = QImage(self.dog.data, self.dog.shape[1], self.dog.shape[0], QImage.Format.Format_Grayscale8).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.dog = self.dog.scaled(label_size.width(), label_size.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        # self.ui.photo_label.resize(label_size)
        self.ui.photo_label.setPixmap(QPixmap.fromImage(self.dog))
        
    @pyqtSlot()
    def display_hough(self):
        self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
        self.get_circles(self.dog, param1=self.ui.param1_spinbox.value(), param2=self.ui.param2_spinbox.value(), min_distance_between_circles=self.ui.min_dist_spinbox.value(), minRadius=self.ui.min_radius_spinbox.value(), maxRadius=self.ui.max_radius_spinbox.value())
        self.image_circles = QImage(self.image_circles.data, self.image_circles.shape[1], self.image_circles.shape[0], QImage.Format.Format_RGB888).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.image_circles = self.image_circles.scaled(label_size.width(), label_size.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        self.ui.photo_label.setPixmap(QPixmap.fromImage(self.image_circles))
        
    def get_dog(self, ksize = 35, sigma = 12, F = 1.1):
        # convert image to grayscale
        gray = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        
        # get gaussian kernel 1
        k1_1d = cv.getGaussianKernel(ksize, sigma)
        k1 = np.dot(k1_1d, k1_1d.T)
        
        # get gaussian kernel 2
        k2_1d = cv.getGaussianKernel(ksize, sigma*F)
        k2 = np.dot(k2_1d, k2_1d.T)
        
        # calculate difference of gaussians
        k = k2 - k1
        
        # apply filter
        dog = cv.filter2D(src=gray, ddepth=-1, kernel=k)
        
        # threshold
        dog[dog < 1] = 0
        dog[dog > 1] = 255
        
        return dog
    
    def get_circles(self, dog, param1=5, param2=12, min_distance_between_circles=100, minRadius=10, maxRadius=30):
        circles = cv.HoughCircles(dog, cv.HOUGH_GRADIENT, 1, minDist=min_distance_between_circles,
                                  param1=param1, param2=param2,
                                  minRadius=minRadius, maxRadius=maxRadius)

        self.image_circles = self.image.copy()
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                center = (i[0], i[1])
                # circle center
                # cv.circle(self.image_circles, center, 1, (0, 100, 100), 3)
                # circle outline
                radius = i[2]
                cv.circle(self.image_circles, center, radius, (255, 0, 255), -1)
                
        return circles
    
    def compute_electrodes(self):
        self.circles = self.get_circles(self.dog,
                                        param1=self.ui.param1_spinbox.value(),
                                        param2=self.ui.param2_spinbox.value(),
                                        min_distance_between_circles=self.ui.min_dist_spinbox.value(),
                                        minRadius=self.ui.min_radius_spinbox.value(),
                                        maxRadius=self.ui.max_radius_spinbox.value())
        
        if self.mesh is not None:
            for circle in self.circles[0, :]:
                vertex = self.get_vertex_from_pixels((circle[0], circle[1]), self.mesh, [4096, 4096])
                id = self.model.get_next_id()
                new_row = pd.DataFrame({
                    "ID": id,
                    "x": vertex[0],
                    "y": vertex[1],
                    "z": vertex[2],
                    "modality": "scan",
                    "label": id
                }, index=[0])
                self.model.insert_point(new_row)

    def onResize(self, _):
        frame_size = self.ui.headmodel_frame.size()
        
        if self.surface_view is not None:
            self.surface_view.resize_view(frame_size.width(), frame_size.height())
        
        if self.dog is not None:
             label_size = self.ui.texture_frame.size()
             self.dog = self.dog.scaled(label_size.width(), label_size.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
             # commented because it distorts the image
             # self.ui.photo_label.setPixmap(QPixmap.fromImage(self.image))

    def onClose(self):
        #Disable the interactor before closing to prevent it
        #from trying to act on already deleted items
        vd.printc("..calling onClose")
        self.vtkWidget_1.close()
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = StartQt6()
    myapp.show()
    sys.exit(app.exec())