from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject


class State(QObject):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.transitions = {}
        self.callbacks = []

    def add_transition(self, signal, state):
        self.transitions[signal] = state

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def apply_callbacks(self):
        for callback in self.callbacks:
            print(f"Applying callback {callback}")
            callback()


class StateMachine(QObject):
    state_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.states = {}
        self.initial_state = None
        self.current_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def add_states(self, states: dict):
        for _, value in states.items():
            self.add_state(value)

    def set_initial_state(self, key):
        self.initial_state = self.states[key]

    def start(self):
        if self.initial_state is None:
            raise ValueError("Initial state not set.")
        self.connect_signals()
        self.transition_to(self.initial_state)

    @pyqtSlot()
    def transition_to(self, state=None):
        if self.sender() is not None and hasattr(self.sender(), "clicked"):
            if self.sender().clicked in self.current_state.transitions.keys():  # type: ignore
                self.current_state = self.current_state.transitions[  # type: ignore
                    self.sender().clicked  # type: ignore
                ]
                self.current_state.apply_callbacks()
                print(f"Transitioning to {self.current_state.name} as callback.")
        elif state:
            self.current_state = state
            self.current_state.apply_callbacks()
            print(f"Transitioning to {self.current_state.name} from argument.")
        # self.state_changed.emit(self.current_state.name)

    def connect_signals(self):
        for state in self.states.values():
            for signal, next_state in state.transitions.items():
                print(f"Connecting signal {signal} to {next_state.name}")
                signal.connect(lambda: self.transition_to(next_state))

    def disconnect_signals(self, state):
        for signal, next_state in state.transitions.items():
            signal.disconnect()

    def __getitem__(self, key):
        if key not in self.states:
            raise KeyError(f"State {key} not found.")
        return self.states[key]

    def finish(self):
        self.current_state = None


def initialize_states(self):
    state_name = "initial_state"
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
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=False,
            t4=False,
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
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t3=True,
        )
    )

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
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t2=True,
        )
    )

    state_name = "texture_loaded"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            display_dog_button=True,
            load_batchfile_button=True,
            load_surface_button=True,
            load_texture_button=True,
            load_mri_button=True,
            load_locations_button=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t1=True,
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

    self.state_machine["surface_loaded"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["mri_loaded"],
    )

    self.state_machine["texture_loaded"].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine["dog_computed"],
    )

    self.state_machine["mri_loaded"].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine["dog_computed"],
    )

    self.state_machine["dog_computed"].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine["hough_displayed"],
    )

    self.state_machine["dog_computed"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["mri_loaded"],
    )

    self.state_machine["hough_displayed"].add_transition(
        self.ui.compute_electrodes_button.clicked,
        self.state_machine["hough_computed"],
    )

    self.state_machine["hough_displayed"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["mri_loaded"],
    )

    # state_name = "surface_loaded"
    # self.state_machine.add_state(State(state_name))
    # self.state_machine[state_name].add_callback(
    #     lambda: self.update_button_states(
    #         display_mri_button=True,
    #         align_scan_button=True,
    #         project_electrodes_button=True,
    #         revert_alignment_button=True,
    #         display_head_button=True,
    #         display_hough_button=True,
    #         compute_electrodes_button=True,
    #         display_dog_button=True,
    #         label_display_button=True,
    #         label_register_button=True,
    #         label_align_button=True,
    #         label_autolabel_button=True,
    #         label_revert_button=True,
    #         label_visualize_correspondence_button=True,
    #         label_label_correspondence_button=True,
    #         label_interpolate_button=True,
    #         load_batchfile_button=True,
    #         load_surface_button=True,
    #         load_texture_button=True,
    #         load_mri_button=True,
    #         load_locations_button=True,
    #         export_locations_button=True,
    #     )
    # )

    # self.state_machine["initial_state"].add_transition(
    #     self.findChild(QPushButton, "load_surface_button").clicked,
    #     self.state_machine["surface_loaded"],
    # )
