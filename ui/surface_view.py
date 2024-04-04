from PyQt6.QtWidgets import QAbstractItemView 

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError:
    raise ImportError('Cannot find the VTK Qt bindings, make sure you have ' \
        'installed them')

from sympy import E
import vedo as vd

from core.electrode import Electrode
from core.cap_model import CapModel

import numpy as np   

from config.colors import ElectrodeColors
from config.sizes import ElectrodeSizes

class SurfaceView(QAbstractItemView):
    """SurfaceView class for displaying a 3D surface in a Qt application."""
    def __init__(self, frame, mesh: vd.Mesh,
                 modality: list[str], config = {}, parent=None):
        super().__init__(parent)
        self._vtk_widget = QVTKRenderWindowInteractor(frame)
        
        self._plotter = vd.Plotter(qt_widget=self._vtk_widget, axes=2)
        
        self.mesh = mesh
        
        self._plotter.add(self.mesh)
        
        self.secondary_mesh = None
        
        if self.mesh is not None:
            self.mesh_centroid = np.mean(self.mesh.points(), 0) # type: ignore
        else:
            self.mesh_centroid = np.array([0, 0, 0])
        
        self.modality = modality
        
        self.config = config
        
    def resize_view(self, width, height):
        self._vtk_widget.resize(width, height)
        
    def setModel(self, model: CapModel):
        self.model: CapModel = model
        self.model.dataChanged.connect(self.dataChanged)
        
    def show(self):
        # msg = vd.Text2D(pos='bottom-left', font="VictorMono") # an empty text
        # self._plotter.show(self.mesh, msg, __doc__)
        self._plotter.show()
        self.render_electrodes()
        
    def render_electrodes(self):
        pass
        
    def get_flagpost(self, text, point: np.ndarray, height: float = 0.005,
                     size: float = 0.2,
                     color: str | tuple[int, int, int] ='r5',
                     background_color: str | tuple[int, int, int] = 'k9') -> vd.Flagpost:
        top_point = ((point-self.mesh_centroid) /
                     np.linalg.norm(point-self.mesh_centroid))*height+point
        fs = vd.Flagpost(text, base=point, top=top_point, c=color, bc=background_color, s=size)       # type: ignore
        return fs
        
    def dataChanged(self, topLeft, bottomRight, roles):
        self.render_electrodes()
    
    def update_config(self, config: dict):
        self.config = config
        self.render_electrodes()
        
    def update_surf_alpha(self, alpha: float):
        self._plotter.actors[0].alpha(alpha)
        self._plotter.render()
        
    def update_secondary_surf_alpha(self, alpha: float):
        self._plotter.actors[1].alpha(alpha)
        self._plotter.render()
        
    def add_secondary_mesh(self, mesh: vd.Mesh):
        self.secondary_mesh = mesh
        self._plotter.add(mesh)
        self._plotter.render()
        self.modality.append("scan")
        
    def reset_secondary_mesh(self):
        self.secondary_mesh = None
        self._plotter.render()
        self.modality = [self.modality[0]]
        
    def remove_secondary_mesh(self):
        if self.secondary_mesh is not None:
            self._plotter.remove(self.secondary_mesh)
            self.secondary_mesh = None
            self._plotter.render()
    
    def close_vtk_widget(self):
        self._vtk_widget.close()


class InteractiveSurfaceView(SurfaceView):
    def __init__(self, frame, mesh: vd.Mesh,
                 modality: list[str], config = {}, parent=None):
        super().__init__(frame, mesh, modality, config, parent)
        
        self._plotter.add_callback('LeftButtonPress', self._on_left_click)
        self._plotter.add_callback('RightButtonPress', self._on_right_click)
        
    def render_electrodes(self):
        self._plotter.clear()
        self._plotter.add(self.mesh)
        if self.secondary_mesh is not None:
            self._plotter.add(self.secondary_mesh)
        
        points_unlabeled = []
        points_labeled = []
        for i in range(self.model.rowCount()):
            electrode_modality = self.model.get_electrode(i).modality
            
            if electrode_modality not in self.modality:
                continue
            
            point = self.model.get_electrode(i).coordinates
            label = self.model.get_electrode(i).label
            
            if electrode_modality == "mri":
                unlabeled_color = ElectrodeColors.MRI_UNLABELED_ELECTRODES_COLOR
                labeled_color = ElectrodeColors.MRI_LABELED_ELECTRODES_COLOR
            else:
                unlabeled_color = ElectrodeColors.HEADSCAN_UNLABELED_ELECTRODES_COLOR
                labeled_color = ElectrodeColors.HEADSCAN_LABELED_ELECTRODES_COLOR
            
            if label is None or label == "" or label == "None":
                self.model.set_electrode_labeled_flag(i, False)
                label = str(i+1)
                points_unlabeled.append((point, label, unlabeled_color))
            else:
                self.model.set_electrode_labeled_flag(i, True)
                points_labeled.append((point, label, labeled_color))
            
        for point, label, color in points_unlabeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c=color, alpha=1) # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point, height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color) # type: ignore
                self._plotter.add(fs)
        
        for point, label, color in points_labeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c=color, alpha=1) # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point,
                    height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color) # type: ignore
                self._plotter.add(fs)
            
        self._plotter.render()
        
    def _on_left_click(self, evt):
        point = evt.picked3d
        if point is not None:
            electrode = Electrode(point,
                                modality=self.modality[0],
                                label="None")
            self.model.insert_electrode(electrode)
            
            self.render_electrodes()
            self.model.layoutChanged.emit()
        
    def _on_right_click(self, evt):
        point = evt.picked3d
        if point is not None:
            self.model.remove_closest_electrode(point, self.modality[0])
            
            self.render_electrodes()
            self.model.layoutChanged.emit()

class LabelingSurfaceView(SurfaceView):
    def __init__(self, frame, mesh: vd.Mesh,
                 modality: list[str], config = {}, parent=None):
        super().__init__(frame, mesh, modality, config, parent)
        
    def render_correspondence_arrows(self, corresponding_electrode_pairs: list[tuple[Electrode, Electrode]]):
        for pair in corresponding_electrode_pairs:
            if pair[0].modality == 'reference' and pair[1].modality in ['scan', 'mri']:
                electrode_A = pair[1]
                electrode_B = pair[0]
            elif pair[1].modality == 'reference' and pair[0].modality in ['scan', 'mri']:
                electrode_A = pair[0]
                electrode_B = pair[1]
            else:
                raise ValueError("Pair of electrodes must contain one reference electrode and one scan/mri electrode.")
            
            arrow = vd.Arrow(
                start_pt=electrode_A.coordinates,
                end_pt=electrode_B.coordinates,
                s=None,
                shaft_radius=None,
                head_radius=None,
                head_length=None,
                res=12,
                c='r4',
                alpha=1.0
                )
            
            self._plotter.add(arrow)
            
        
    def render_electrodes(self):
        self._plotter.clear()
        self._plotter.add(self.mesh)
        if self.secondary_mesh is not None:
            self._plotter.add(self.secondary_mesh)
        
        points_unlabeled = []
        points_labeled = []
        for i in range(self.model.rowCount()):
            electrode_modality = self.model.get_electrode(i).modality
            
            point = self.model.get_electrode(i).unit_sphere_cartesian_coordinates
            label = self.model.get_electrode(i).label
            
            if electrode_modality == "reference":
                labeled_color = ElectrodeColors.LABELING_REFERENCE_ELECTRODES_COLOR
                unlabeled_color = '#000000'
            else:
                unlabeled_color = ElectrodeColors.LABELING_MEASURED_UNLABELED_ELECTRODES_COLOR
                labeled_color = ElectrodeColors.LABELING_MEASURED_LABELED_ELECTRODES_COLOR
            
            if label is None or label == "" or label == "None":
                self.model.set_electrode_labeled_flag(i, False)
                label = str(i+1)
                points_unlabeled.append((point, label, unlabeled_color))
            else:
                self.model.set_electrode_labeled_flag(i, True)
                points_labeled.append((point, label, labeled_color))
            
        for point, label, color in points_unlabeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c=color, alpha=1) # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point, height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color) # type: ignore
                self._plotter.add(fs)
        
        for point, label, color in points_labeled:
            sphere = vd.Sphere(
                point,
                r=self.config["sphere_size"],
                res=8, c=color, alpha=1) # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label, point,
                    height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color) # type: ignore
                self._plotter.add(fs)
            
        self._plotter.render()
        