from .state_machine import States

from .state_machine import States


def initialize_fileio_transitions(self):
    # Transitions from INITIAL state
    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.LOCATIONS_LOADED.value],
    )

    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_LOADED_NO_LOCS.value],
    )

    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.MRI_LOADED_NO_LOCS.value],
    )

    # Transitions from LOCATIONS_LOADED
    self.state_machine[States.LOCATIONS_LOADED.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_LOADED.value],
    )

    self.state_machine[States.LOCATIONS_LOADED.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.MRI_LOADED.value],
    )

    # Transitions from MRI_LOADED
    self.state_machine[States.MRI_LOADED.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED.value],
    )

    # Transitions from SURFACE_LOADED
    self.state_machine[States.SURFACE_LOADED.value].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_LOADED.value],
    )

    self.state_machine[States.SURFACE_LOADED.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED.value],
    )

    # Transitions from SURFACE_WITH_MRI_LOADED
    self.state_machine[States.SURFACE_WITH_MRI_LOADED.value].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED.value],
    )

    # Transitions from SURFACE_TEXTURE_LOADED
    self.state_machine[States.SURFACE_TEXTURE_LOADED.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED.value],
    )

    # Transitions from SURFACE_LOADED_NO_LOCS
    self.state_machine[States.SURFACE_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.SURFACE_LOADED.value],
    )

    self.state_machine[States.SURFACE_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_LOADED_NO_LOCS.value],
    )

    # Transitions from SURFACE_TEXTURE_LOADED_NO_LOCS
    self.state_machine[States.SURFACE_TEXTURE_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS.value],
    )

    self.state_machine[States.SURFACE_TEXTURE_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_LOADED.value],
    )

    # Transitions from SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS
    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED.value],
    )

    # Transitions from SURFACE_LOADED_NO_LOCS to SURFACE_WITH_MRI_LOADED_NO_LOCS
    self.state_machine[States.SURFACE_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value],
    )

    # Transitions from MRI_LOADED_NO_LOCS
    self.state_machine[States.MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value],
    )

    # Transitions from SURFACE_WITH_MRI_LOADED_NO_LOCS
    self.state_machine[States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED.value],
    )

    # Transitions from MRI_LOADED_NO_LOCS to MRI_LOADED
    self.state_machine[States.MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.MRI_LOADED.value],
    )


def setup_master_state_reset(self):
    # Transition from all states (except INITIAL) to the initial state
    states_to_reset = [
        States.LOCATIONS_LOADED,
        States.SURFACE_LOADED,
        States.MRI_LOADED,
        States.SURFACE_WITH_MRI_LOADED,
        States.SURFACE_TEXTURE_LOADED,
        States.SURFACE_TEXTURE_WITH_MRI_LOADED,
        States.SURFACE_LOADED_NO_LOCS,
        States.SURFACE_TEXTURE_LOADED_NO_LOCS,
        States.SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS,
        States.MRI_LOADED_NO_LOCS,
        States.SURFACE_WITH_MRI_LOADED_NO_LOCS,
        States.SURFACE_PROCESSING_NO_LOCS,
        States.MRI_PROCESSING_NO_LOCS,
        States.SURFACE_PROCESSING,
        States.LABELING_SURFACE,
        States.QC_SURFACE,
        States.MRI_PROCESSING,
        States.LABELING_MRI,
        States.QC_MRI,
        States.SURFACE_WITH_MRI_PROCESSING,
        States.LABELING_SURFACE_WITH_MRI,
        States.SURFACE_TO_MRI_ALIGNMENT,
        States.TEXTURE_DOG,
        States.TEXTURE_HOUGH,
        States.TEXTURE_HOUGH_COMPUTED,
        States.SURFACE_TEXTURE_PROCESSING,
        States.LABELING_SURFACE_TEXTURE,
        States.QC_SURFACE_TEXTURE,
        States.TEXTURE_WITH_MRI_DOG,
        States.TEXTURE_WITH_MRI_HOUGH,
        States.TEXTURE_WITH_MRI_HOUGH_COMPUTED,
        States.SURFACE_TEXTURE_WITH_MRI_PROCESSING,
        States.LABELING_SURFACE_TEXTURE_WITH_MRI,
        States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT,
        States.TEXTURE_DOG_NO_LOCS,
        States.TEXTURE_HOUGH_NO_LOCS,
        States.TEXTURE_HOUGH_COMPUTED_NO_LOCS,
        States.SURFACE_TEXTURE_PROCESSING_NO_LOCS,
        States.TEXTURE_WITH_MRI_DOG_NO_LOCS,
        States.TEXTURE_WITH_MRI_HOUGH_NO_LOCS,
        States.TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS,
        States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS,
        States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS,
        States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS,
        States.SURFACE_TO_MRI_ALIGNMENT_NO_LOCS,
    ]

    for state in states_to_reset:
        self.state_machine[state.value].add_transition(
            self.ui.restart_button_0.clicked,
            self.state_machine[States.INITIAL.value],
        )


def setup_surface_processing_no_locs_transitions(self):
    # Path 1:
    # SURFACE_LOADED_NO_LOCS -- proceed_button_0 --> SURFACE_PROCESSING_NO_LOCS
    self.state_machine[States.SURFACE_LOADED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_PROCESSING_NO_LOCS.value],
    )
    self.state_machine[States.SURFACE_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_LOADED_NO_LOCS.value],
    )


def setup_mri_processing_no_locs_transitions(self):
    # Path 2:
    # MRI_LOADED_NO_LOCS -- proceed_button_0 --> MRI_PROCESSING_NO_LOCS
    self.state_machine[States.MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.MRI_PROCESSING_NO_LOCS.value],
    )
    self.state_machine[States.MRI_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.MRI_LOADED_NO_LOCS.value],
    )


def setup_surface_processing_transitions(self):
    # Path 3:
    # SURFACE_LOADED -- proceed_button_0 --> SURFACE_PROCESSING
    # SURFACE_PROCESSING -- proceed_button_2 --> LABELING_SURFACE
    # LABELING_SURFACE -- proceed_button_4 --> QC_SURFACE
    self.state_machine[States.SURFACE_LOADED.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE.value],
    )
    self.state_machine[States.LABELING_SURFACE.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.QC_SURFACE.value],
    )
    # Reverse transitions:
    self.state_machine[States.SURFACE_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_LOADED.value],
    )
    self.state_machine[States.LABELING_SURFACE.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_PROCESSING.value],
    )
    self.state_machine[States.QC_SURFACE.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE.value],
    )


def setup_mri_processing_transitions(self):
    # Path 4:
    # MRI_LOADED -- proceed_button_0 --> MRI_PROCESSING
    # MRI_PROCESSING -- proceed_button_3 --> LABELING_MRI
    # LABELING_MRI -- proceed_button_4 --> QC_MRI
    self.state_machine[States.MRI_LOADED.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.MRI_PROCESSING.value],
    )
    self.state_machine[States.MRI_PROCESSING.value].add_transition(
        self.ui.proceed_button_3.clicked,
        self.state_machine[States.LABELING_MRI.value],
    )
    self.state_machine[States.LABELING_MRI.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.QC_MRI.value],
    )
    # Reverse transitions:
    self.state_machine[States.MRI_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.MRI_LOADED.value],
    )
    self.state_machine[States.LABELING_MRI.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.MRI_PROCESSING.value],
    )
    self.state_machine[States.QC_MRI.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.LABELING_MRI.value],
    )


def setup_surface_with_mri_processing_transitions(self):
    # Path 5:
    # SURFACE_WITH_MRI_LOADED -- proceed_button_0 --> SURFACE_WITH_MRI_PROCESSING
    # SURFACE_WITH_MRI_PROCESSING -- proceed_button_2 --> LABELING_SURFACE_WITH_MRI
    # LABELING_SURFACE_WITH_MRI -- proceed_button_4 --> SURFACE_TO_MRI_ALIGNMENT
    self.state_machine[States.SURFACE_WITH_MRI_LOADED.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE_WITH_MRI.value],
    )
    self.state_machine[States.LABELING_SURFACE_WITH_MRI.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT.value],
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED.value],
    )
    self.state_machine[States.LABELING_SURFACE_WITH_MRI.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.LABELING_SURFACE_WITH_MRI.value],
    )


def setup_texture_processing_transitions(self):
    # Path 6:
    # SURFACE_TEXTURE_LOADED -- proceed_button_0 --> TEXTURE_DOG
    # TEXTURE_DOG -- display_dog_button --> TEXTURE_HOUGH
    # TEXTURE_HOUGH -- display_hough_button --> TEXTURE_HOUGH_COMPUTED
    # TEXTURE_HOUGH_COMPUTED -- proceed_button_1 --> SURFACE_TEXTURE_PROCESSING
    # SURFACE_TEXTURE_PROCESSING -- proceed_button_2 --> LABELING_SURFACE_TEXTURE
    # LABELING_SURFACE_TEXTURE -- proceed_button_4 --> QC_SURFACE_TEXTURE

    # Example implementation (replace with actual transition setup code):
    self.state_machine[States.SURFACE_TEXTURE_LOADED.value].add_transition(
        self.ui.proceed_button_0.clicked, self.state_machine[States.TEXTURE_DOG.value]
    )
    self.state_machine[States.TEXTURE_DOG.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_HOUGH.value],
    )
    self.state_machine[States.TEXTURE_HOUGH.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_HOUGH_COMPUTED.value],
    )
    self.state_machine[States.TEXTURE_HOUGH_COMPUTED.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_TEXTURE_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_TEXTURE_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked, self.state_machine[States.LABELING_SURFACE_TEXTURE.value]
    )
    self.state_machine[States.LABELING_SURFACE_TEXTURE.value].add_transition(
        self.ui.proceed_button_4.clicked, self.state_machine[States.QC_SURFACE_TEXTURE.value]
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_TEXTURE_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked, self.state_machine[States.TEXTURE_DOG.value]
    )
    self.state_machine[States.LABELING_SURFACE_TEXTURE.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_TEXTURE_PROCESSING.value],
    )
    self.state_machine[States.QC_SURFACE_TEXTURE.value].add_transition(
        self.ui.restart_button_2.clicked, self.state_machine[States.LABELING_SURFACE_TEXTURE.value]
    )


def setup_texture_with_mri_processing_transitions(self):
    # Path 7:

    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_DOG.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_DOG.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_HOUGH.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_HOUGH.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE_TEXTURE_WITH_MRI.value],
    )
    self.state_machine[States.LABELING_SURFACE_TEXTURE_WITH_MRI.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT.value],
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_DOG.value],
    )
    self.state_machine[States.LABELING_SURFACE_TEXTURE_WITH_MRI.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value],
    )
    self.state_machine[States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.LABELING_SURFACE_TEXTURE_WITH_MRI.value],
    )


def setup_texture_processing_no_locs_transitions(self):
    # Path 8:

    self.state_machine[States.SURFACE_TEXTURE_LOADED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.TEXTURE_DOG_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_DOG_NO_LOCS.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_HOUGH_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_HOUGH_NO_LOCS.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_HOUGH_COMPUTED_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_HOUGH_COMPUTED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_TEXTURE_PROCESSING_NO_LOCS.value],
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_TEXTURE_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.TEXTURE_DOG_NO_LOCS.value],
    )


def setup_texture_with_mri_processing_no_locs_transitions(self):
    # Path 9:

    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_DOG_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_DOG_NO_LOCS.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_NO_LOCS.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS.value],
    )
    self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS.value],
    )
    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS.value],
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_DOG_NO_LOCS.value],
    )
    self.state_machine[States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS.value],
    )


def setup_surface_with_mri_processing_no_locs_transitions(self):
    # Path 10:

    self.state_machine[States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS.value],
    )
    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT_NO_LOCS.value],
    )

    # Reverse transitions:
    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value],
    )
    self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT_NO_LOCS.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS.value],
    )
