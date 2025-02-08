from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject
from enum import Enum


class States(Enum):
    # File I/O states
    INITIAL = "INITIAL"
    LOCATIONS_LOADED = "LOCATIONS_LOADED"
    SURFACE_LOADED = "SURFACE_LOADED"
    SURFACE_TEXTURE_LOADED = "SURFACE_TEXTURE_LOADED"
    MRI_LOADED = "MRI_LOADED"
    SURFACE_WITH_MRI_LOADED = "SURFACE_WITH_MRI_LOADED"
    SURFACE_LOADED_NO_LOCS = "SURFACE_LOADED_NO_LOCS"
    SURFACE_TEXTURE_LOADED_NO_LOCS = "SURFACE_TEXTURE_LOADED_NO_LOCS"
    MRI_LOADED_NO_LOCS = "MRI_LOADED_NO_LOCS"
    SURFACE_WITH_MRI_LOADED_NO_LOCS = "SURFACE_WITH_MRI_LOADED_NO_LOCS"
    SURFACE_TEXTURE_WITH_MRI_LOADED = "SURFACE_TEXTURE_WITH_MRI_LOADED"
    SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS = "SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS"

    # Processing states (existing)
    TEXTURE_DOG = "TEXTURE_DOG"
    TEXTURE_WITH_MRI_DOG = "TEXTURE_WITH_MRI_DOG"
    TEXTURE_HOUGH = "TEXTURE_HOUGH"
    TEXTURE_WITH_MRI_HOUGH = "TEXTURE_WITH_MRI_HOUGH"
    TEXTURE_HOUGH_COMPUTED = "TEXTURE_HOUGH_COMPUTED"
    TEXTURE_WITH_MRI_HOUGH_COMPUTED = "TEXTURE_WITH_MRI_HOUGH_COMPUTED"
    SURFACE_PROCESSING = "SURFACE_PROCESSING"
    SURFACE_PROCESSING_NO_LOCS = "SURFACE_PROCESSING_NO_LOCS"
    MRI_PROCESSING = "MRI_PROCESSING"
    MRI_PROCESSING_NO_LOCS = "MRI_PROCESSING_NO_LOCS"
    SURFACE_WITH_MRI_PROCESSING = "SURFACE_WITH_MRI_PROCESSING"

    SURFACE_TEXTURE_PROCESSING = "SURFACE_TEXTURE_PROCESSING"
    SURFACE_TEXTURE_WITH_MRI_PROCESSING = "SURFACE_TEXTURE_WITH_MRI_PROCESSING"

    # New processing states for no locations (paths 8, 9, 10)
    TEXTURE_DOG_NO_LOCS = "TEXTURE_DOG_NO_LOCS"
    TEXTURE_HOUGH_NO_LOCS = "TEXTURE_HOUGH_NO_LOCS"
    TEXTURE_HOUGH_COMPUTED_NO_LOCS = "TEXTURE_HOUGH_COMPUTED_NO_LOCS"

    TEXTURE_WITH_MRI_DOG_NO_LOCS = "TEXTURE_WITH_MRI_DOG_NO_LOCS"
    TEXTURE_WITH_MRI_HOUGH_NO_LOCS = "TEXTURE_WITH_MRI_HOUGH_NO_LOCS"
    TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS = "TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS"

    SURFACE_TEXTURE_PROCESSING_NO_LOCS = "SURFACE_TEXTURE_PROCESSING_NO_LOCS"
    SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS = "SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS"
    SURFACE_WITH_MRI_PROCESSING_NO_LOCS = "SURFACE_WITH_MRI_PROCESSING_NO_LOCS"

    # New alignment and QC states for texture with MRI and surface with MRI (paths 7, 9, 10)
    SURFACE_TEXTURE_TO_MRI_ALIGNMENT = "SURFACE_TEXTURE_TO_MRI_ALIGNMENT"
    QC_SURFACE_TEXTURE_WITH_MRI = "QC_SURFACE_TEXTURE_WITH_MRI"
    SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS = "SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS"
    QC_SURFACE_TEXTURE_WITH_MRI_NO_LOCS = "QC_SURFACE_TEXTURE_WITH_MRI_NO_LOCS"
    SURFACE_TO_MRI_ALIGNMENT_NO_LOCS = "SURFACE_TO_MRI_ALIGNMENT_NO_LOCS"
    QC_SURFACE_WITH_MRI_NO_LOCS = "QC_SURFACE_WITH_MRI_NO_LOCS"

    # Labeling and QC states (existing)
    LABELING_MRI = "LABELING_MRI"
    LABELING_SURFACE = "LABELING_SURFACE"
    LABELING_SURFACE_TEXTURE = "LABELING_SURFACE_TEXTURE"
    LABELING_SURFACE_WITH_MRI = "LABELING_SURFACE_WITH_MRI"
    LABELING_SURFACE_TEXTURE_WITH_MRI = "LABELING_SURFACE_TEXTURE_WITH_MRI"
    QC_SURFACE = "QC_SURFACE"
    QC_MRI = "QC_MRI"
    QC_SURFACE_WITH_MRI = "QC_SURFACE_WITH_MRI"
    QC_SURFACE_TEXTURE = "QC_SURFACE_TEXTURE"
    SURFACE_TO_MRI_ALIGNMENT = "SURFACE_TO_MRI_ALIGNMENT"


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

    def __init__(self, statusbar):
        super().__init__()
        self.states = {}
        self.initial_state = None
        self.current_state = None

        self.statusbar = statusbar

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
                self.statusbar.showMessage(f"State: {self.current_state.name}")
        elif state:
            self.current_state = state
            self.current_state.apply_callbacks()
            print(f"Transitioning to {self.current_state.name} from argument.")
            self.statusbar.showMessage(f"State: {self.current_state.name}")

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
