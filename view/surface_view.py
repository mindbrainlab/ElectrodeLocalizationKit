from PyQt6.QtWidgets import QAbstractItemView

try:
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
except ImportError:
    raise ImportError(
        "Cannot find the VTK Qt bindings, make sure you have " "installed them"
    )

import vedo as vd

from model.cap_model import CapModel

import numpy as np

from config.mappings import ModalitiesMapping


class SurfaceView(QAbstractItemView):
    """SurfaceView class for displaying a 3D surface in a Qt application."""

    def __init__(
        self, frame, mesh: vd.Mesh, modality: list[str], config={}, parent=None
    ):
        super().__init__(parent)

        self.frame = frame
        self._vtk_widget = QVTKRenderWindowInteractor(frame)

        self._plotter = vd.Plotter(qt_widget=self._vtk_widget, axes=2)

        self.mesh = mesh

        self._plotter.add(self.mesh)

        self.secondary_mesh = None

        if self.mesh is not None:
            self.mesh_centroid = np.mean(self.mesh.points(), 0)  # type: ignore
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

    def get_flagpost(
        self,
        text,
        point: np.ndarray,
        height: float = 0.005,
        size: float = 0.2,
        color: str | tuple[int, int, int] = "r5",
        background_color: str | tuple[int, int, int] = "k",
    ) -> vd.Flagpost:
        top_point = (
            (point - self.mesh_centroid) / np.linalg.norm(point - self.mesh_centroid)
        ) * height + point
        fs = vd.Flagpost(text, base=point, top=top_point, c=color, bc=background_color, s=size)  # type: ignore
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
        self.modality.append(ModalitiesMapping.HEADSCAN)

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
