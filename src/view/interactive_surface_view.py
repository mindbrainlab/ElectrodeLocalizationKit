import vedo as vd
import time

from view.surface_view import SurfaceView

from data_models.electrode import Electrode
from data_models.cap_model import CapModel

from config.colors import ElectrodeColors
from config.mappings import ModalitiesMapping

from ui.label_dialog import LabelingDialog


class InteractiveSurfaceView(SurfaceView):
    def __init__(
        self,
        frame,
        mesh: vd.Mesh,
        modality: list[str],
        config={},
        model: CapModel | None = None,
        parent=None,
    ):
        super().__init__(frame, mesh, modality, config, model, parent)

        self._interaction_state = "x"

        self.click_start_time = 0
        self._plotter.add_callback("LeftButtonPress", self._on_left_click)
        self._plotter.add_callback("LeftButtonRelease", self._on_left_click_release)
        self._plotter.add_callback("KeyPress", self._on_keypress)

        self.text_state = vd.Text2D(
            "View Mode",
            c="black",
            s=0.8,
            pos="top-left",
        )
        self._plotter.add(self.text_state)

    def render_electrodes(self):
        self._plotter.clear()
        self._plotter.add(self.mesh)
        if self.secondary_mesh is not None:
            self._plotter.add(self.secondary_mesh)

        points_unlabeled = []
        points_labeled = []
        for i in range(self.model.rowCount()):
            electrode = self.model.get_electrode(i)

            if electrode.modality not in self.modality:
                continue

            point = self.model.get_electrode(i).coordinates
            label = self.model.get_electrode(i).label

            if electrode.modality == ModalitiesMapping.MRI:
                unlabeled_color = ElectrodeColors.MRI_UNLABELED_ELECTRODES_COLOR
                labeled_color = ElectrodeColors.MRI_LABELED_ELECTRODES_COLOR
                if electrode.fiducial:
                    unlabeled_color = ElectrodeColors.MRI_FIDUCIALS_COLOR
                    labeled_color = ElectrodeColors.MRI_FIDUCIALS_COLOR
            else:
                unlabeled_color = ElectrodeColors.HEADSCAN_UNLABELED_ELECTRODES_COLOR
                labeled_color = ElectrodeColors.HEADSCAN_LABELED_ELECTRODES_COLOR
                if electrode.fiducial:
                    unlabeled_color = ElectrodeColors.HEADSCAN_FIDUCIALS_COLOR
                    labeled_color = ElectrodeColors.HEADSCAN_FIDUCIALS_COLOR

            if label is None or label == "" or label == "None":
                self.model.set_electrode_labeled_flag(i, False)
                label = str(i + 1)
                points_unlabeled.append((point, label, unlabeled_color))
            else:
                self.model.set_electrode_labeled_flag(i, True)
                points_labeled.append((point, label, labeled_color))

        for point, label, color in points_unlabeled:
            sphere = vd.Sphere(point, r=self.config["sphere_size"], res=8, c=color, alpha=1)  # type: ignore
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
            sphere = vd.Sphere(point, r=self.config["sphere_size"], res=8, c=color, alpha=1)  # type: ignore
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

        self._plotter.render()

    def _on_left_click(self, evt):
        self.click_start_time = time.time()

    def _on_left_click_release(self, evt):
        stop_time = time.time()
        if stop_time - self.click_start_time > 0.2:
            return

        point = evt.picked3d
        if point is not None and evt.keyPressed is not None:
            if self._interaction_state == "s":
                electrode = Electrode(point, modality=self.modality[0], label="None")
                self.model.insert_electrode(electrode)
            elif self._interaction_state == "d":
                self.model.remove_closest_electrode(point, self.modality[0], include_fiducials=True)
            elif self._interaction_state == "a":
                labels = [
                    electrode.label
                    for electrode in self.model.get_electrodes_by_modality(
                        [ModalitiesMapping.REFERENCE]
                    )
                    if electrode.label is not None and electrode.label != "None"
                ]
                labeled_electrode_labels = [
                    electrode.label
                    for electrode in self.model.get_labeled_electrodes([self.modality[0]])
                ]
                unlabeled = list(set(labels) - set(labeled_electrode_labels))
                # sort the labels
                unlabeled.sort()
                dialog = LabelingDialog(unlabeled)
                dialog.exec()
                label = dialog.get_electrode_label()
                self.model.label_closest_electrode(point, label, self.modality[0])
            elif self._interaction_state == "e":
                labels = [
                    electrode.label
                    for electrode in self.model.get_electrodes_by_modality(
                        [ModalitiesMapping.REFERENCE]
                    )
                    if electrode.label is not None and electrode.label != "None"
                ]
                labeled_electrode_labels = [
                    electrode.label
                    for electrode in self.model.get_labeled_electrodes([self.modality[0]])
                ]
                unlabeled = list(set(labels) - set(labeled_electrode_labels))
                # sort the labels
                unlabeled.sort()
                dialog = LabelingDialog(unlabeled)
                dialog.exec()
                label = dialog.get_electrode_label()
                electrode = Electrode(point, modality=self.modality[0], label=label)
                self.model.insert_electrode(electrode)
            elif self._interaction_state == "E":
                dialog = LabelingDialog()
                dialog.exec()
                label = dialog.get_electrode_label()
                electrode = Electrode(point, modality=self.modality[0], label=label, fiducial=True)
                self.model.insert_electrode(electrode)
            elif self._interaction_state == "x":
                evt.keyPressed = None
                evt.keypress = None
            else:
                return
            self.render_electrodes()
            self.model.layoutChanged.emit()

    def _on_keypress(self, evt):
        if evt.keyPressed is not None:
            if evt.keyPressed == "x":
                self._interaction_state = "x"
                self._plotter.background(c1="white", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "View Mode",
                    c="black",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)
            elif evt.keyPressed == "s":
                self._interaction_state = "s"
                self._plotter.background(c1="#b1fcb3", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "Select Mode",
                    c="green",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)
            elif evt.keyPressed == "d":
                self._interaction_state = "d"
                self._plotter.background(c1="#fcb1b1", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "Delete Mode",
                    c="red",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)
            elif evt.keyPressed == "a":
                self._interaction_state = "a"
                self._plotter.background(c1="#b1e1fc", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "Label Mode",
                    c="blue",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)
            elif evt.keyPressed == "e":
                self._interaction_state = "e"
                self._plotter.background(c1="#ffc069", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "Select+Label Mode",
                    c="orange",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)
            elif evt.keyPressed == "E":
                self._interaction_state = "E"
                self._plotter.background(c1="#9ab8a0", c2="white")
                evt.keyPressed = None
                evt.keypress = None
                self._plotter.remove(self.text_state)
                self.text_state = vd.Text2D(
                    "Fiducials Mode",
                    c="#006e16",
                    s=0.8,
                    pos="top-left",
                )
                self._plotter.add(self.text_state)

            else:
                return
            self.render_electrodes()
