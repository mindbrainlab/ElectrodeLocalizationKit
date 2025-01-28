from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject
from enum import Enum


class States(Enum):
    INITIAL = "initial_state"
    LOCATIONS_LOADED = "locations_loaded"
    SURFACE_READY = "surface_ready"
    SURFACE_TEXTURE_READY = "surface_texture_ready"
    MRI_READY = "mri_ready"
    SURFACE_MRI_READY = "surface_mri_ready"
    SURFACE_TEXTURE_MRI_READY = "surface_texture_mri_ready"
    TEXTURE_PROCESSING_DOG = "texture_processing_dog"
    TEXTURE_WITH_MRI_PROCESSING_DOG = "texture_with_mri_processing_dog"
    TEXTURE_PROCESSING_HOUGH = "texture_processing_hough"
    TEXTURE_WITH_MRI_PROCESSING_HOUGH = "texture_with_mri_processing_hough"
    TEXTURE_HOUGH_COMPUTED = "texture_hough_computed"
    TEXTURE_WITH_MRI_HOUGH_COMPUTED = "texture_with_mri_hough_computed"
    SURFACE_PROCESSING = "surface_processing"
    SURFACE_WITH_MRI_PROCESSING = "surface_with_mri_processing"
    MRI_PROCESSING = "mri_processing"
    LABELING_SURFACE = "labeling_surface"
    LABELING_MRI = "labeling_mri"
    LABELING_SURFACE_WITH_MRI = "labeling_surface_with_mri"
    MRI_ALIGNMENT = "mri_alignment"
    QC_SURFACE = "qc_surface"
    QC_MRI = "qc_mri"


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
