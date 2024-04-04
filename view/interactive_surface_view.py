import vedo as vd

from view.surface_view import SurfaceView

from model.electrode import Electrode

from config.colors import ElectrodeColors
from config.mappings import ModalitiesMapping

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
            
            if electrode_modality == ModalitiesMapping.MRI:
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