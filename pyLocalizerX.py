from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QErrorMessage, QTableWidgetItem
from PyQt6.QtGui import QFont, QFontDatabase

from PyQt6.QtCore import QModelIndex, Qt, pyqtSlot, QAbstractTableModel

from PyQt6.QtWidgets import QAbstractItemView

from ui.pyloc_main_window import Ui_MainWindow

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vedo as vd
from icecream import ic

import sys
from time import sleep
import numpy as np
import pandas as pd

import cv2 as cv

from core.cap_model import CapModel
from core.electrode import Electrode

from ui.surface_view import SurfaceView
        

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._plotter = None
        self._labels = []

    def set_plotter(self, plotter):
        self._plotter = plotter
        
    def set_labels(self, labels):
        self._labels = labels        

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)

    def insert_point(self, row, parent=QModelIndex()):
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data = pd.concat([self._data, row])
        self.endInsertRows()
        return True
    
    def remove_point(self, id, parent=QModelIndex()):
        self.beginRemoveRows(parent, self.rowCount(), self.rowCount())
        self._data = self._data[self._data.ID != id]
        self.endRemoveRows()
        return True
    
    def remove_closest_point(self, point_to_remove):
        dists = []
        for point in self._data[['x', 'y', 'z']].values:
            dists.append(np.linalg.norm(point-point_to_remove))
        
        if len(dists) > 0:      
            min_idx = np.argmin(dists)
            id_to_remove = self._data.iloc[min_idx]['ID']
            self.remove_point(id_to_remove)
    
    def get_next_id(self):
        numeric_ids = [int(x) for x in self._data.ID.to_list() if x.isdigit()]
        if len(numeric_ids) == 0:
            return '0'
        else:    
            return str(np.max(numeric_ids) + 1)
    
    def render(self) -> None:
        if self._plotter is None:
            raise ValueError('Plotter not set')
        
        points_unlabeled = []
        points_labeled = []
        for row in self._data.iterrows():
            if row[1]['label'] in self._labels:
                points_labeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
            else:
                points_unlabeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
        
        # remove all actors except the mesh and the text
        # for actor in self._plotter.actors:
        #     if isinstance(actor, vd.Mesh) == False and isinstance(actor, vd.Text2D) == False:
        #         self._plotter.remove(actor)
        
        if len(self._plotter.actors) > 2:
            self._plotter.remove(self._plotter.actors[2:])
        
        if len(points_unlabeled) > 0:
            spheres = vd.Spheres(points_unlabeled, r=0.004, res=8, c='r5', alpha=1)
            self._plotter.add(spheres)
        
        if len(points_labeled) > 0:
            spheres = vd.Spheres(points_labeled, r=0.004, res=8, c='b5', alpha=1)
            self._plotter.add(spheres)
            
        self._plotter.render()
            
        self.layoutChanged.emit()
        
    # def dataChanged(self, index, index2, roles):
    #     ic("Data changed")
        # self.layoutChanged.emit()
        # self.render()
    #     return True
    
    def rotate_xyz_of_data_by_x_degrees(self, degrees):
        # extract xyz from _data
        xyz = self._data[['x', 'y', 'z']].values
        # create a rotation matrix (do not use vd)
        theta = np.radians(degrees)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((1, 0, 0), (0, c, -s), (0, s, c)))
        # rotate xyz
        xyz_rotated = np.dot(xyz, R)
        # update _data
        self._data[['x', 'y', 'z']] = xyz_rotated

    def setData(self, index, value, role):
        id("setData")
        if role == Qt.ItemDataRole.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.render()
            return True
        return False

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._data.columns[col]

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

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

        # data = pd.DataFrame([[1, 9, 2], [1, 0, -1], [3, 5, 2], [3, 3, 2], [5, 8, 9],], columns=["A", "B", "C"])
        # create an empyt dataframe with columns ID, x, y, z, modality
        data = pd.DataFrame(columns=["ID", "x", "y", "z", "modality", "label"])
        self.model = PandasModel(data)

        data = [Electrode([0.1, 0.2, 0.3], modality="scan", ID=1, label="1"),
                Electrode([0.4, 0.5, 0.6], modality="scan", ID=2, label="2")]
        self.model = CapModel([])

        self.ui.electrodes_table.setModel(self.model)
        # for column_hidden in (1, 2, 3):
        #     self.ui.electrodes_table.hideColumn(column_hidden)

        # prepare vedo canvas
        self.vtkWidget_1 = QVTKRenderWindowInteractor(self.ui.headmodel_frame)
        
        self.plt = vd.Plotter(qt_widget=self.vtkWidget_1)
        self.plt.add_callback('LeftButtonPress', self.on_left_click)
        self.plt.add_callback('RightButtonPress', self.on_right_click)
        
        self.my_vtk = SurfaceView(self.ui.headmodel_frame)
        self.my_vtk.setModel(self.model)
        
        # connect signals and slots
        self.ui.load_surface_button.clicked.connect(self.load_surface)
        self.ui.load_texture_button.clicked.connect(self.load_texture)
        self.ui.display_head_button.clicked.connect(self.display_surface)
        
        self.ui.display_dog_button.clicked.connect(self.display_dog)
        self.ui.kernel_size_spinbox.valueChanged.connect(self.display_dog)
        self.ui.sigma_spinbox.valueChanged.connect(self.display_dog)
        self.ui.diff_factor_spinbox.valueChanged.connect(self.display_dog)
        
        self.ui.display_hough_button.clicked.connect(self.display_hough)
        self.ui.param1_spinbox.valueChanged.connect(self.display_hough)
        self.ui.param2_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_dist_spinbox.valueChanged.connect(self.display_hough)
        self.ui.min_radius_spinbox.valueChanged.connect(self.display_hough)
        self.ui.max_radius_spinbox.valueChanged.connect(self.display_hough)
        
        self.ui.compute_electrodes_button.clicked.connect(self.compute_electrodes)
        
        self.ui.process_table_button.clicked.connect(self.process_table)
        
        # self.model.dataChanged.connect(self.model.render)
        
        self.image = None
        self.dog = None
        
        self.circles = None
        
        # temporary
        self.surface_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.obj'
        self.texture_file = '/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg'
        
        if self.surface_file and self.texture_file:
            self.mesh= vd.Mesh(self.surface_file).texture(self.texture_file)
        
        self.ui.centralwidget.resizeEvent = self.onResize
        
        self.points = []
        
        # set status bar
        self.ui.statusbar.showMessage('Welcome!')

    def process_table(self):
        self.model.rotate_xyz_of_data_by_x_degrees(10)
        
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
        self.my_vtk.set_mesh(self.mesh)
        
        frame_size = self.ui.headmodel_frame.size()
        self.my_vtk.resize(frame_size.width(), frame_size.height())
        
        self.my_vtk.show()
        
        # frame_size = self.ui.headmodel_frame.size()
        # self.vtkWidget_1.resize(frame_size.width(), frame_size.height())
        
        # msg = vd.Text2D(pos='bottom-left', font="VictorMono") # an empty text
        
        # self.plt.show(self.mesh, msg, __doc__)
        
        # self.model.set_plotter(self.plt)
        # self.model.set_labels(['2', '6', '8'])
        # self.model.render()

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
        
        id = self.model.get_next_id()
        
        if pt is not None:  
            # new_row = pd.DataFrame([[self.model.get_next_id(),
            #                             pt[0], pt[1], pt[2],
            #                             "scan", False]],
            #                         columns=["ID", "x", "y", "z" , "modality", "label"])
            new_row = pd.DataFrame({
                "ID": id,
                "x": pt[0],
                "y": pt[1],
                "z": pt[2],
                "modality": "scan",
                "label": id
            }, index=[0])
            self.model.insert_point(new_row)
            self.model.render()

    def on_right_click(self, evt):
        print("right click")
        pt = evt.picked3d
        
        if pt is not None:
            self.model.remove_closest_point(pt)
            self.model.render()
            
    # def on_left_click(self, evt):
    #     print("left click")
    #     pt = evt.picked3d
        
    #     if pt is not None:
    #         self.points.append(pt)
            
    #         pts = vd.Spheres(self.points, r=0.005, res=8, c='r5', alpha=1)
            
    #         if len(self.plt.actors) > 2:
    #             self.plt.pop()
    #         self.plt.add(pts).render() 
            
    #         n_points = len(self.points)
    #         pt_id = n_points - 1
            
    #         new_row = pd.DataFrame([[pt_id, pt[0], pt[1], pt[2], "scan"]], columns=["ID", "x", "y", "z" , "modality"])
    #         # self.model._data = pd.concat([self.model._data, new_row])
    #         # self.model.layoutChanged.emit()
    #         self.model.insert_point(new_row)
            
    #     ic(self.points)

    # def on_right_click(self, evt):
    #     print("right click")
    #     pt = evt.picked3d
        
    #     ic(self.points)
        
    #     if pt is not None:
    #         self.remove_closest_point(pt)
            
    #         ic(self.plt.actors)
            
    #         if len(self.plt.actors) > 2:
    #             self.plt.pop()
            
    #         if len(self.points) > 0:
    #             pts = vd.Spheres(self.points, r=0.005, res=8, c='r5', alpha=1)
    #             self.plt.add(pts).render()
    #         else:
    #             self.plt.render()
        
    #     ic(self.points)
        
    # def remove_closest_point(self, pt):
    #     dists = []
    #     for p in self.points:
    #         dists.append(np.linalg.norm(p-pt))
            
    #     ic(dists)
            
    #     min_dist = np.min(dists)
    #     min_idx = np.argmin(dists)
    #     print(min_dist)
    #     print(min_idx)
    #     self.points.pop(min_idx)
        

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
        
    @QtCore.pyqtSlot()
    def display_hough(self):
        self.dog = self.get_dog(ksize=self.ui.kernel_size_spinbox.value(), sigma=self.ui.sigma_spinbox.value(), F=self.ui.diff_factor_spinbox.value())
        self.get_circles(self.dog, param1=self.ui.param1_spinbox.value(), param2=self.ui.param2_spinbox.value(), min_distance_between_circles=self.ui.min_dist_spinbox.value(), minRadius=self.ui.min_radius_spinbox.value(), maxRadius=self.ui.max_radius_spinbox.value())
        self.image_circles = QtGui.QImage(self.image_circles.data, self.image_circles.shape[1], self.image_circles.shape[0], QtGui.QImage.Format.Format_RGB888).rgbSwapped()
        
        label_size = self.ui.texture_frame.size()
        self.image_circles = self.image_circles.scaled(label_size.width(), label_size.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

        self.ui.photo_label.setPixmap(QtGui.QPixmap.fromImage(self.image_circles))
        
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