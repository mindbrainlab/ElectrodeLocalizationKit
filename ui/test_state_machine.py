from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStatusBar,
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject


class StateMachine:
    def __init__(self):
        self.states = {}  # Dictionary to hold states and their transitions
        self.current_state = None

    def add_state(self, name, action=None):
        self.states[name] = action

    def set_state(self, name):
        if name in self.states:
            self.current_state = name
            action = self.states[name]
            if action:
                action()
        else:
            print(f"State '{name}' not found.")

    def get_state(self):
        return self.current_state


state_machine = StateMachine()

state_machine.add_state(
    "initial_state",
    lambda: self.update_button_states(
        display_mri_button=False,
        align_scan_button=False,
        project_electrodes_button=False,
        revert_alignment_button=False,
        display_head_button=False,
        display_hough_button=False,
        compute_electrodes_button=False,
        display_dog_button=False,
        label_display_button=False,
        label_register_button=False,
        label_align_button=False,
        label_autolabel_button=False,
        label_revert_button=False,
        label_visualize_correspondence_button=False,
        label_label_correspondence_button=False,
        label_interpolate_button=False,
        load_batchfile_button=True,
        load_surface_button=True,
        load_texture_button=False,
        load_mri_button=True,
        load_locations_button=True,
        export_locations_button=False,
    ),
)


def initialize_states(self):
    state_name = "initial_state"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback()

    state_name = "surface_loaded"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            display_mri_button=False,
            align_scan_button=False,
            project_electrodes_button=False,
            revert_alignment_button=False,
            display_head_button=True,
            display_hough_button=False,
            compute_electrodes_button=False,
            display_dog_button=False,
            label_display_button=False,
            label_register_button=False,
            label_align_button=False,
            label_autolabel_button=False,
            label_revert_button=False,
            label_visualize_correspondence_button=False,
            label_label_correspondence_button=False,
            label_interpolate_button=False,
            load_batchfile_button=True,
            load_surface_button=True,
            load_texture_button=True,
            load_mri_button=True,
            load_locations_button=True,
            export_locations_button=False,
        )
    )

    state_name = "mri_loaded"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            display_mri_button=True,
            align_scan_button=False,
            project_electrodes_button=False,
            revert_alignment_button=False,
            display_head_button=False,
            display_hough_button=False,
            compute_electrodes_button=False,
            display_dog_button=False,
            label_display_button=False,
            label_register_button=False,
            label_align_button=False,
            label_autolabel_button=False,
            label_revert_button=False,
            label_visualize_correspondence_button=False,
            label_label_correspondence_button=False,
            label_interpolate_button=False,
            load_batchfile_button=True,
            load_surface_button=True,
            load_texture_button=True,
            load_mri_button=True,
            load_locations_button=True,
            export_locations_button=False,
        )
    )

    state_name = "texture_loaded"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            display_mri_button=False,
            align_scan_button=False,
            project_electrodes_button=False,
            revert_alignment_button=False,
            display_head_button=False,
            display_hough_button=False,
            compute_electrodes_button=False,
            display_dog_button=True,
            label_display_button=False,
            label_register_button=False,
            label_align_button=False,
            label_autolabel_button=False,
            label_revert_button=False,
            label_visualize_correspondence_button=False,
            label_label_correspondence_button=False,
            label_interpolate_button=False,
            load_batchfile_button=True,
            load_surface_button=True,
            load_texture_button=True,
            load_mri_button=True,
            load_locations_button=True,
            export_locations_button=False,
        )
    )

    state_name = "dog_computed"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            display_hough_button=True,
            compute_electrodes_button=False,
        )
    )

    state_name = "hough_displayed"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            compute_electrodes_button=True,
            export_locations_button=True,
        )
    )

    state_name = "hough_computed"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            export_locations_button=True,
        )
    )

    # transitions
    self.state_machine["initial_state"].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine["surface_loaded"],
    )

    self.state_machine["initial_state"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["mri_loaded"],
    )

    self.state_machine["surface_loaded"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["texture_loaded"],
    )

    self.state_machine["texture_loaded"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["dog_computed"],
    )

    self.state_machine["dog_computed"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["hough_displayed"],
    )

    self.state_machine["hough_displayed"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["hough_computed"],
    )
