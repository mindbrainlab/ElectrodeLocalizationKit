from .state_machine import States


def initialize_transitions(self):
    # transitions from initial state

    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_locations_button.clicked,
        self.state_machine[States.LOCATIONS_LOADED.value],
    )

    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_READY.value],
    )

    self.state_machine[States.INITIAL.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.MRI_READY.value],
    )

    # transitions to data ready states

    self.state_machine[States.LOCATIONS_LOADED.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_READY.value],
    )

    self.state_machine[States.SURFACE_READY.value].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_READY.value],
    )

    self.state_machine[States.SURFACE_TEXTURE_READY.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_MRI_READY.value],
    )

    self.state_machine[States.LOCATIONS_LOADED.value].add_transition(
        self.ui.load_mri_button.clicked,
        self.state_machine[States.MRI_READY.value],
    )

    self.state_machine[States.MRI_READY.value].add_transition(
        self.ui.load_surface_button.clicked,
        self.state_machine[States.SURFACE_MRI_READY.value],
    )

    self.state_machine[States.SURFACE_MRI_READY.value].add_transition(
        self.ui.load_texture_button.clicked,
        self.state_machine[States.SURFACE_TEXTURE_MRI_READY.value],
    )

    # transitions to initial state
    for state_name in [
        States.SURFACE_READY,
        States.SURFACE_TEXTURE_READY,
        States.MRI_READY,
        States.SURFACE_MRI_READY,
        States.SURFACE_TEXTURE_MRI_READY,
        States.LOCATIONS_LOADED,
        States.SURFACE_PROCESSING,
        States.SURFACE_WITH_MRI_PROCESSING,
        States.TEXTURE_PROCESSING_DOG,
        States.TEXTURE_WITH_MRI_PROCESSING_DOG,
        States.TEXTURE_PROCESSING_HOUGH,
        States.TEXTURE_WITH_MRI_PROCESSING_HOUGH,
        States.MRI_PROCESSING,
    ]:
        self.state_machine[state_name.value].add_transition(
            self.ui.restart_button_0.clicked,
            self.state_machine[States.INITIAL.value],
        )

    # transitions to texture processing
    self.state_machine[States.SURFACE_TEXTURE_READY.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.TEXTURE_PROCESSING_DOG.value],
    )

    self.state_machine[States.SURFACE_TEXTURE_MRI_READY.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_PROCESSING_DOG.value],
    )

    self.state_machine[States.TEXTURE_PROCESSING_DOG.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_PROCESSING_HOUGH.value],
    )

    self.state_machine[States.TEXTURE_WITH_MRI_PROCESSING_DOG.value].add_transition(
        self.ui.display_dog_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_PROCESSING_HOUGH.value],
    )

    self.state_machine[States.TEXTURE_PROCESSING_HOUGH.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_HOUGH_COMPUTED.value],
    )

    self.state_machine[States.TEXTURE_WITH_MRI_PROCESSING_HOUGH.value].add_transition(
        self.ui.display_hough_button.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value],
    )

    # transitions to surface processing
    self.state_machine[States.SURFACE_READY.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_PROCESSING.value],
    )

    self.state_machine[States.TEXTURE_HOUGH_COMPUTED.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_PROCESSING.value],
    )

    self.state_machine[States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value].add_transition(
        self.ui.proceed_button_1.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value],
    )

    self.state_machine[States.SURFACE_MRI_READY.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value],
    )

    # transitions to mri processing
    self.state_machine[States.MRI_READY.value].add_transition(
        self.ui.proceed_button_0.clicked,
        self.state_machine[States.MRI_PROCESSING.value],
    )

    self.state_machine[States.LABELING_MRI.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.MRI_PROCESSING.value],
    )

    # transitions to labeling
    self.state_machine[States.MRI_PROCESSING.value].add_transition(
        self.ui.proceed_button_3.clicked,
        self.state_machine[States.LABELING_MRI.value],
    )

    self.state_machine[States.SURFACE_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE.value],
    )

    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.proceed_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE_WITH_MRI.value],
    )

    # transitions from labeling to mri
    self.state_machine[States.LABELING_SURFACE_WITH_MRI.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT.value],
    )

    # transitions from labeling to qc
    self.state_machine[States.LABELING_SURFACE.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.QC_SURFACE.value],
    )

    self.state_machine[States.LABELING_MRI.value].add_transition(
        self.ui.proceed_button_4.clicked,
        self.state_machine[States.QC_MRI.value],
    )

    self.state_machine[States.SURFACE_TO_MRI_ALIGNMENT.value].add_transition(
        self.ui.proceed_button_3.clicked,
        self.state_machine[States.QC_SURFACE_WITH_MRI.value],
    )

    # transition from surface states back to appropriate texture state on restart_button_2
    self.state_machine[States.SURFACE_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_READY.value],
    )

    self.state_machine[States.SURFACE_TEXTURE_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.TEXTURE_PROCESSING_DOG.value],
    )

    self.state_machine[States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.TEXTURE_WITH_MRI_PROCESSING_DOG.value],
    )

    self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.SURFACE_MRI_READY.value],
    )

    # transition from labeling states back to appropriate surface state on restart_button_4
    self.state_machine[States.LABELING_SURFACE.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_PROCESSING.value],
    )

    self.state_machine[States.LABELING_SURFACE_WITH_MRI.value].add_transition(
        self.ui.restart_button_4.clicked,
        self.state_machine[States.SURFACE_WITH_MRI_PROCESSING.value],
    )

    # transition from QC states back to appropriate labeling state on restart_button_2 and restart_button_3
    self.state_machine[States.QC_SURFACE.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.LABELING_SURFACE.value],
    )

    self.state_machine[States.QC_SURFACE_WITH_MRI.value].add_transition(
        self.ui.restart_button_3.clicked,
        self.state_machine[States.LABELING_SURFACE_WITH_MRI.value],
    )

    self.state_machine[States.QC_MRI.value].add_transition(
        self.ui.restart_button_2.clicked,
        self.state_machine[States.LABELING_MRI.value],
    )
