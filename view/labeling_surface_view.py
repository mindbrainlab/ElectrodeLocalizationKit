import vedo as vd

from view.surface_view import SurfaceView

from model.electrode import Electrode

from config.colors import ElectrodeColors
from config.mappings import ModalitiesMapping


class LabelingSurfaceView(SurfaceView):
    def __init__(
        self, frame, mesh: vd.Mesh, modality: list[str], config={}, parent=None
    ):
        super().__init__(frame, mesh, modality, config, parent)
        self.arrows = []

    def generate_correspondence_arrows(
        self, corresponding_electrode_pairs: list[tuple[Electrode, Electrode]]
    ):
        self.arrows = []
        for pair in corresponding_electrode_pairs:
            if pair[0].modality == ModalitiesMapping.REFERENCE and pair[1].modality in [
                ModalitiesMapping.HEADSCAN,
                ModalitiesMapping.MRI,
            ]:
                electrode_A = pair[0]
                electrode_B = pair[1]
            elif pair[1].modality == ModalitiesMapping.REFERENCE and pair[
                0
            ].modality in [ModalitiesMapping.HEADSCAN, ModalitiesMapping.MRI]:
                electrode_A = pair[1]
                electrode_B = pair[0]
            else:
                raise ValueError(
                    "Pair of electrodes must contain one reference electrode and one scan/mri electrode."
                )

            arrow = vd.Arrow(
                start_pt=electrode_A.unit_sphere_cartesian_coordinates,
                end_pt=electrode_B.unit_sphere_cartesian_coordinates,
                s=0.001,
                shaft_radius=None,
                head_radius=None,
                head_length=None,
                res=12,
                c="#56fc03",
                alpha=1.0,
            )

            self.arrows.append(arrow)

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
                unlabeled_color = "#000000"
            else:
                unlabeled_color = (
                    ElectrodeColors.LABELING_MEASURED_UNLABELED_ELECTRODES_COLOR
                )
                labeled_color = (
                    ElectrodeColors.LABELING_MEASURED_LABELED_ELECTRODES_COLOR
                )

            if label is None or label == "" or label == "None":
                self.model.set_electrode_labeled_flag(i, False)
                label = str(i + 1)
                points_unlabeled.append((point, label, unlabeled_color))
            else:
                self.model.set_electrode_labeled_flag(i, True)
                points_labeled.append((point, label, labeled_color))

        for point, label, color in points_unlabeled:
            sphere = vd.Sphere(
                point, r=self.config["sphere_size"], res=8, c=color, alpha=1
            )  # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label,
                    point,
                    height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color,
                )  # type: ignore
                self._plotter.add(fs)

        for point, label, color in points_labeled:
            sphere = vd.Sphere(
                point, r=self.config["sphere_size"], res=8, c=color, alpha=1
            )  # type: ignore
            self._plotter.add(sphere)
            if self.config["draw_flagposts"]:
                fs = self.get_flagpost(
                    label,
                    point,
                    height=self.config["flagpost_height"],
                    size=self.config["flagpost_size"],
                    color=color,
                )  # type: ignore
                self._plotter.add(fs)

        for arrow in self.arrows:
            self._plotter.add(arrow)

        self._plotter.render()
