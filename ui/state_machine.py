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
    # initial states

    state_name = "initial_state"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_texture_button=False,
            load_mri_button=False,
            load_locations_button=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=False,
            t4=False,
            t5=False,
        )
    )

    state_name = "locations_loaded"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=True,
            load_texture_button=False,
            load_mri_button=True,
            load_locations_button=True,
        )
    )

    state_name = "surface_ready"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=True,
        )
    )

    state_name = "surface_texture_ready"
    self.state_machine.add_state(State(state_name))

    state_name = "mri_ready"
    self.state_machine.add_state(State(state_name))

    state_name = "surface_mri_ready"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=True,
        )
    )

    state_name = "surface_texture_mri_ready"
    self.state_machine.add_state(State(state_name))

    # processing mode states

    state_name = "texture_processing_dog"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=True,
            t2=False,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_texture_tab_states(
            t0=True,
            t1=False,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(1))

    state_name = "texture_with_mri_processing_dog"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=True,
            t2=False,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_texture_tab_states(
            t0=True,
            t1=False,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(1))

    state_name = "texture_processing_hough"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=True,
            t2=False,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_texture_tab_states(
            t0=True,
            t1=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(1))
    self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(0))

    state_name = "texture_with_mri_processing_hough"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=True,
            t2=False,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_texture_tab_states(
            t0=True,
            t1=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(1))
    self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(0))

    state_name = "surface_processing"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=True,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))

    state_name = "surface_with_mri_processing"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=True,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))

    state_name = "mri_processing"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=True,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(3))

    state_name = "labeling_surface"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=False,
            t4=True,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(4))

    state_name = "labeling_mri"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=False,
            t4=True,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(4))

    state_name = "labeling_surface_with_mri"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=False,
            t4=True,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(4))

    state_name = "mri_alignment"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=True,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(3))

    state_name = "qc_surface"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=True,
            t3=False,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))

    state_name = "qc_mri"
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(
            t0=True,
            t1=False,
            t2=False,
            t3=True,
            t4=False,
            t5=True,
        )
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(3))

    # transitions from initial state

    self.state_machine["initial_state"].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine["locations_loaded"],
    )

    # transitions to data ready states

    self.state_machine["locations_loaded"].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine["surface_ready"],
    )

    self.state_machine["surface_ready"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["surface_texture_ready"],
    )

    self.state_machine["surface_texture_ready"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["surface_texture_mri_ready"],
    )

    self.state_machine["locations_loaded"].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine["mri_ready"],
    )

    self.state_machine["mri_ready"].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine["surface_mri_ready"],
    )

    self.state_machine["surface_mri_ready"].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine["surface_texture_mri_ready"],
    )

    # transitions to initial state
    for state_name in [
        "surface_ready",
        "surface_texture_ready",
        "mri_ready",
        "surface_mri_ready",
        "surface_texture_mri_ready",
        "locations_loaded",
        "surface_processing",
        "surface_with_mri_processing",
        "texture_processing_dog",
        "texture_with_mri_processing_dog",
        "texture_processing_hough",
        "texture_with_mri_processing_hough",
        "mri_processing",
    ]:
        self.state_machine[state_name].add_transition(
            self.ui.restart_button_0.clicked,
            self.state_machine["initial_state"],
        )

    # transitions to texture processing
    self.state_machine["surface_texture_ready"].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine["texture_processing_dog"],
    )

    self.state_machine["surface_texture_mri_ready"].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine["texture_with_mri_processing_dog"],
    )

    self.state_machine["texture_processing_dog"].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine["texture_processing_hough"],
    )

    self.state_machine["texture_with_mri_processing_dog"].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine["texture_with_mri_processing_hough"],
    )

    # transitions to surface processing
    self.state_machine["surface_ready"].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine["surface_processing"],
    )

    self.state_machine["texture_processing_hough"].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine["surface_processing"],
    )

    self.state_machine["texture_with_mri_processing_hough"].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine["surface_with_mri_processing"],
    )

    self.state_machine["surface_mri_ready"].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine["surface_with_mri_processing"],
    )

    # transitions to mri processing
    self.state_machine["mri_ready"].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine["mri_processing"],
    )

    self.state_machine["labeling_mri"].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine["mri_processing"],
    )

    # transitions to labeling
    self.state_machine["mri_processing"].add_transition(
        self.ui.proceed_button_3.clicked,
        self.state_machine["labeling_mri"],
    )

    self.state_machine["surface_processing"].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine["labeling_surface"],
    )

    self.state_machine["surface_with_mri_processing"].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine["labeling_surface_with_mri"],
    )

    # transitions from labeling to mri
    self.state_machine["labeling_surface_with_mri"].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine["mri_alignment"],
    )

    # transitions from labeling to qc
    self.state_machine["labeling_surface"].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine["qc_surface"],
    )

    self.state_machine["labeling_mri"].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine["qc_mri"],
    )

    self.state_machine["mri_alignment"].add_transition(
        self.ui.proceed_button_3.clicked,
        self.state_machine["qc_surface"],
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
