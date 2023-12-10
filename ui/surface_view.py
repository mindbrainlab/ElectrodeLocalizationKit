from PyQt6.QtWidgets import QAbstractItemView 
from typing import Optional
from fsspec import FSTimeoutError

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError:
    raise ImportError('Cannot find the VTK Qt bindings, make sure you have ' \
        'installed them')

import vedo as vd

from core.electrode import Electrode
from core.cap_model import CapModel

import numpy as np

class SurfaceView(QAbstractItemView):
    """SurfaceView class for displaying a 3D surface in a Qt application."""
    def __init__(self, frame, mesh: Optional[vd.Mesh] = None,
                 modality: str = "", config = {}, parent=None):
        super().__init__(parent)
        self._vtk_widget = QVTKRenderWindowInteractor(frame)
        
        self._plotter = vd.Plotter(qt_widget=self._vtk_widget, axes=2)
        self._plotter.add_callback('LeftButtonPress', self._on_left_click)
        self._plotter.add_callback('RightButtonPress', self._on_right_click)
        
        self.mesh = mesh
        
        if self.mesh is not None:
            self.mesh_centroid = np.mean(self.mesh.points(), 0) # type: ignore
        else:
            self.mesh_centroid = np.array([0, 0, 0])
        
        self.modality = modality
        
        self.config = config
        self._set_config_defaults()
        
    def resize_view(self, width, height):
        self._vtk_widget.resize(width, height)
        
    def setModel(self, model: CapModel):
        self.model: CapModel = model
        self.model.dataChanged.connect(self.dataChanged)
        
    def show(self):
        msg = vd.Text2D(pos='bottom-left', font="VictorMono") # an empty text
        self._plotter.show(self.mesh, msg, __doc__)
        self.render_electrodes()
        
    def render_electrodes(self):
        if len(self._plotter.actors) > 2:
            self._plotter.remove(self._plotter.actors[2:])
        
        points_unlabeled = []
        points_labeled = []
        for i in range(self.model.rowCount()):
            if self.model.get_electrode(i).modality != self.modality:
                continue
            point = self.model.get_electrode(i).coordinates
            label = self.model.get_electrode(i).label
            if label is None or label == "" or label == "None":
                label = str(i+1)
                points_unlabeled.append((point, label))
            else:
                points_labeled.append((point, label))
            
        for point, label in points_unlabeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c='r5', alpha=1)
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point, height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color='r5')
                self._plotter.add(fs)
        
        for point, label in points_labeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c='b5', alpha=1)
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point,
                    height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color='b5')
                self._plotter.add(fs)
            
        self._plotter.render()
        
    def get_flagpost(self, text, point: np.ndarray, height: float = 0.005,
                     size: float = 0.2, color: str ='r5') -> vd.Flagpost:
        top_point = ((point-self.mesh_centroid) /
                     np.linalg.norm(point-self.mesh_centroid))*height+point
        fs = vd.Flagpost(text, base=point, top=top_point, c=color, s=size)       # type: ignore
        return fs
        
    def _on_left_click(self, evt):
        point = evt.picked3d
        if point is not None:
            electrode = Electrode(point,
                                modality=self.modality,
                                label="None")
            self.model.insert_electrode(electrode)
            
            self.render_electrodes()
            self.model.layoutChanged.emit()
        
    def _on_right_click(self, evt):
        point = evt.picked3d
        if point is not None:
            self.model.remove_closest_electrode(point, self.modality)
            
            self.render_electrodes()
            self.model.layoutChanged.emit()
        
    def dataChanged(self, topLeft, bottomRight, roles):
        self.render_electrodes()
        return True
    
    def update_config(self, config: dict):
        self.config = config
        self.render_electrodes()
        
    def update_surf_alpha(self, alpha: float):
        self._plotter.actors[0].alpha(alpha)
        self._plotter.render()
        
    def _set_config_defaults(self):
        self.config.setdefault("sphere_size", 0.02)
        self.config.setdefault("draw_flagposts", False)
        self.config.setdefault("flagpost_size", 0.6)
        self.config.setdefault("flagpost_height", 0.05)
    
    def close_vtk_widget(self):
        self._vtk_widget.close()