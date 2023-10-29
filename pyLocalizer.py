from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QErrorMessage, QTableWidgetItem
from PyQt6.QtGui import QFont, QFontDatabase

from PyQt6.QtCore import Qt, pyqtSlot

from ui.pyloc_main_window import Ui_MainWindow

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vedo as vd
from icecream import ic

import sys
from time import sleep
import numpy as np
import pandas as pd

import cv2 as cv

class StartQt6(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # set states and stuff
        # self.data_loaded = False
        # self.connection_established = False
        # --> states should enable and disable widgets
        #         e.g. self.ui.slider.setDisabled(True)

        # prepare vedo canvas
        ic(self.ui.headmodel_frame)
        self.vtkWidget_1 = QVTKRenderWindowInteractor(self.ui.headmodel_frame)
        
        self.plt = vd.Plotter(qt_widget=self.vtkWidget_1)
        self.plt.add_callback('LeftButtonPress', self.on_left_click)
        self.plt.add_callback('RightButtonPress', self.on_right_click)
        
        # connect signals and slots
        self.ui.load_surface_button.clicked.connect(self.load_surface)
        self.ui.load_texture_button.clicked.connect(self.load_texture)
        self.ui.display_head_button.clicked.connect(self.display_surface)
        
        self.ui.display_dog_button.clicked.connect(self.display_dog)
        
        self.ui.kernel_size_spinbox.valueChanged.connect(self.display_dog)
        self.ui.sigma_spinbox.valueChanged.connect(self.display_dog)
        self.ui.diff_factor_spinbox.valueChanged.connect(self.display_dog)
        
        self.image = None
        self.dog = None
        
        # temporary
        self.surface_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj'
        self.texture_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg'
        
        self.ui.centralwidget.resizeEvent = self.onResize
        
        self.points = []
        
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
        if self.surface_file and self.texture_file:
            frame_size = self.ui.headmodel_frame.size()
            self.vtkWidget_1.resize(frame_size.width(), frame_size.height())
            self.mesh= vd.Mesh(self.surface_file).texture(self.texture_file)
            

            
            vertex = self.get_vertex_from_pixels([840, 1115], self.mesh, [4096, 4096])
            pts = vd.Spheres([vertex], r=0.005, res=8, c='r5', alpha=1)
            
            msg = vd.Text2D(pos='bottom-left', font="VictorMono") # an empty text
            
            self.plt.show(self.mesh, msg, __doc__)
            self.plt.add(pts).render() 

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
            
    def on_left_click(self, evt):
        print("left click")
        pt = evt.picked3d
        
        if pt is not None:
            self.points.append(pt)
            
            pts = vd.Spheres(self.points, r=0.005, res=8, c='r5', alpha=1)
            
            if len(self.plt.actors) > 3:
                self.plt.pop()
            self.plt.add(pts).render() 
            
        ic(self.plt)
        ic(self.points)

    def on_right_click(self, evt):
        print("right click")
        pt = evt.picked3d
        
        ic(self.points)
        
        if pt is not None:
            self.remove_closest_point(pt)
                
            pts = vd.Spheres(self.points, r=0.005, res=8, c='r5', alpha=1)
            
            if len(self.plt.actors) > 3:
                self.plt.pop()
            self.plt.add(pts).render()
            
        ic(self.plt)
        ic(self.points)
        
    def remove_closest_point(self, pt):
        dists = []
        for p in self.points:
            dists.append(np.linalg.norm(p-pt))
        min_dist = np.min(dists)
        min_idx = np.argmin(dists)
        print(min_dist)
        print(min_idx)
        self.points.pop(min_idx)

    # @pyqtSlot()
    # def onClick(self):
    #     vd.printc("..calling onClick")
    #     self.plt.actors[0].color('red').rotate_z(40)
    #     self.plt.interactor.Render()

    @QtCore.pyqtSlot()
    def display_dog(self):
        if self.image is None:
            self.image = cv.imread(self.texture_file)
            self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
            self.dog = QtGui.QImage(self.dog.data, self.dog.shape[1], self.dog.shape[0], QtGui.QImage.Format.Format_Grayscale8).rgbSwapped()
        else:
            self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
            self.dog = QtGui.QImage(self.dog.data, self.dog.shape[1], self.dog.shape[0], QtGui.QImage.Format.Format_Grayscale8).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.dog = self.dog.scaled(label_size.width(), label_size.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        # self.ui.photo_label.resize(label_size)
        self.ui.photo_label.setPixmap(QtGui.QPixmap.fromImage(self.dog))
        
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

    def onResize(self, _):
        frame_size = self.ui.headmodel_frame.size()
        self.vtkWidget_1.resize(frame_size.width(), frame_size.height())
        
        if self.dog is not None:
             label_size = self.ui.texture_frame.size()
             self.dog = self.dog.scaled(label_size.width(), label_size.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
             # commented because it distorts the image
             # self.ui.photo_label.setPixmap(QtGui.QPixmap.fromImage(self.image))

    def onClose(self):
        #Disable the interactor before closing to prevent it
        #from trying to act on already deleted items
        vd.printc("..calling onClose")
        self.vtkWidget_1.close()
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = StartQt6()
    myapp.show()
    sys.exit(app.exec())