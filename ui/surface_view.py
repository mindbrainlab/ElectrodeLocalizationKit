from PyQt6.QtWidgets import QAbstractItemView 
from typing import Optional

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError:
    raise ImportError('Cannot find the VTK Qt bindings, make sure you have installed them')

import vedo as vd

from core.electrode import Electrode
from core.cap_model import CapModel

class SurfaceView(QAbstractItemView):
    """SurfaceView class for displaying a 3D surface in a Qt application."""
    def __init__(self, frame, mesh: Optional[vd.Mesh] = None, modality: str = "", parent=None):
        super().__init__(parent)
        self._vtk_widget = QVTKRenderWindowInteractor(frame)
        
        self._plotter = vd.Plotter(qt_widget=self._vtk_widget)
        self._plotter.add_callback('LeftButtonPress', self._on_left_click)
        self._plotter.add_callback('RightButtonPress', self._on_right_click)
        
        self.mesh = mesh
        
        self.modality = modality
        
    def resize_view(self, width, height):
        self._vtk_widget.resize(width, height)
        
    def setModel(self, model: CapModel):
        self.model: CapModel = model
        self.model.dataChanged.connect(self.dataChanged)
        
    def show(self):
        msg = vd.Text2D(pos='bottom-left', font="VictorMono") # an empty text
        self._plotter.show(self.mesh, msg, __doc__)
        self._render_electrodes()
        
    def _render_electrodes(self):
        if len(self._plotter.actors) > 2:
            self._plotter.remove(self._plotter.actors[2:])
        
        points_unlabeled = []
        points_labeled = []
        for i in range(self.model.rowCount()):
            point = self.model.get_electrode(i).coordinates
            label = self.model.get_electrode(i).label
            if label is None or label == "" or label == "None":
                points_unlabeled.append(point)
            else:
                points_labeled.append(point)
                
        if len(points_unlabeled) > 0:
            spheres = vd.Spheres(points_unlabeled, r=0.004, res=8, c='r5', alpha=1)
            self._plotter.add(spheres)
        
        if len(points_labeled) > 0:
            spheres = vd.Spheres(points_labeled, r=0.004, res=8, c='b5', alpha=1)
            self._plotter.add(spheres)
            
        self._plotter.render()
        
    def _on_left_click(self, evt):
        point = evt.picked3d
        if point is not None:
            eID = self.model.get_next_id()
            electrode = Electrode(point,
                                modality=self.modality,
                                eID=eID,
                                label="None")
            self.model.insert_electrode(electrode)
            
            self._render_electrodes()
            self.model.layoutChanged.emit()
        
    def _on_right_click(self, evt):
        point = evt.picked3d
        if point is not None:
            self.model.remove_closest_electrode(point)
            
            self._render_electrodes()
            self.model.layoutChanged.emit()
        
    def dataChanged(self, topLeft, bottomRight, roles):
        self._render_electrodes()
        return True