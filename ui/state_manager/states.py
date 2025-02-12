from config.mappings import ModalitiesMapping
from .state_machine import States, State


def initialize_fileio_states(self):
    # INITIAL state
    state_name = States.INITIAL.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=True,
            load_texture_button=False,
            load_mri_button=True,
            load_locations_button=True,
            proceed_button_0=False,
        )
    )
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=False, t4=False, t5=False)
    )
    self.state_machine[state_name].add_callback(lambda: self.set_data_containers())
    self.state_machine[state_name].add_callback(lambda: self.model.clear())

    # LOCATIONS_LOADED state
    state_name = States.LOCATIONS_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=True,
            load_texture_button=False,
            load_mri_button=True,
            load_locations_button=False,
        )
    )

    # SURFACE_LOADED (with locations)
    state_name = States.SURFACE_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_texture_button=True,
            load_mri_button=True,
            load_locations_button=False,
            proceed_button_0=True,
        )
    )

    # SURFACE_LOADED (no locations)
    state_name = States.SURFACE_LOADED_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_texture_button=True,
            load_mri_button=True,
            proceed_button_0=True,
        )
    )

    # MRI_LOADED (with locations)
    state_name = States.MRI_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_mri_button=False,
            load_surface_button=True,
            load_locations_button=False,
            proceed_button_0=True,
        )
    )

    # MRI_LOADED (no locations)
    state_name = States.MRI_LOADED_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_mri_button=False,
            load_surface_button=True,
            proceed_button_0=True,
        )
    )

    # SURFACE_WITH_MRI_LOADED (with locations)
    state_name = States.SURFACE_WITH_MRI_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_mri_button=False,
            load_texture_button=True,
            load_locations_button=False,
            proceed_button_0=True,
        )
    )

    # SURFACE_WITH_MRI_LOADED (no locations)
    state_name = States.SURFACE_WITH_MRI_LOADED_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_mri_button=False,
            load_texture_button=True,
            proceed_button_0=True,
        )
    )

    # SURFACE_TEXTURE_LOADED (with locations)
    state_name = States.SURFACE_TEXTURE_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=False,
            load_mri_button=True,
            load_locations_button=False,
            proceed_button_0=True,
        )
    )

    # SURFACE_TEXTURE_LOADED (no locations)
    state_name = States.SURFACE_TEXTURE_LOADED_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=False,
            load_mri_button=True,
            proceed_button_0=True,
        )
    )

    # SURFACE_TEXTURE_WITH_MRI_LOADED (with locations)
    state_name = States.SURFACE_TEXTURE_WITH_MRI_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=False,
            load_mri_button=False,
            load_locations_button=False,
            proceed_button_0=True,
        )
    )

    # SURFACE_TEXTURE_WITH_MRI_LOADED (no locations)
    state_name = States.SURFACE_TEXTURE_WITH_MRI_LOADED_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=False,
            load_mri_button=False,
            proceed_button_0=True,
        )
    )


def initialize_processing_states(self):
    # -------------------------------
    # Texture Processing – DOG
    for state_name in [
        States.TEXTURE_DOG.value,
        States.TEXTURE_WITH_MRI_DOG.value,
        States.TEXTURE_DOG_NO_LOCS.value,
        States.TEXTURE_WITH_MRI_DOG_NO_LOCS.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_tab_states(t0=True, t1=True, t2=False, t3=False, t4=False, t5=True)
        )
        self.state_machine[state_name].add_callback(
            lambda: self.update_texture_tab_states(t0=True, t1=False)
        )
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(proceed_button_1=False)
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_tab(1))
        self.state_machine[state_name].add_callback(
            lambda: self.model.clear_electrodes_by_modality(ModalitiesMapping.HEADSCAN)
        )

    # Texture Processing – HOUGH
    for state_name in [
        States.TEXTURE_HOUGH.value,
        States.TEXTURE_WITH_MRI_HOUGH.value,
        States.TEXTURE_HOUGH_NO_LOCS.value,
        States.TEXTURE_WITH_MRI_HOUGH_NO_LOCS.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_tab_states(t0=True, t1=True, t2=False, t3=False, t4=False, t5=True)
        )
        self.state_machine[state_name].add_callback(
            lambda: self.update_texture_tab_states(t0=True, t1=True)
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(0))

    # Texture Hough Computed states
    for state_name in [
        States.TEXTURE_HOUGH_COMPUTED.value,
        States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value,
        States.TEXTURE_HOUGH_COMPUTED_NO_LOCS.value,
        States.TEXTURE_WITH_MRI_HOUGH_COMPUTED_NO_LOCS.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(proceed_button_1=True)
        )

    # -------------------------------
    # Surface Processing (with locations)
    for state_name in [
        States.SURFACE_TEXTURE_PROCESSING.value,
        States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(restart_button_2=True, proceed_button_2=True)
        )

    for state_name in [
        States.SURFACE_PROCESSING.value,
        States.SURFACE_WITH_MRI_PROCESSING.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(restart_button_2=False, proceed_button_2=True)
        )

    # Surface Processing (no locations)
    state_name = States.SURFACE_PROCESSING_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(restart_button_2=False, proceed_button_2=False)
    )

    # -------------------------------
    # MRI Processing (with locations)
    state_name = States.MRI_PROCESSING.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(3))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(restart_button_3=True, proceed_button_3=True)
    )

    # MRI Processing (no locations)
    state_name = States.MRI_PROCESSING_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(3))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(restart_button_3=False, proceed_button_3=False)
    )

    # Processing states (no locations) for surface texture processing
    state_name = States.SURFACE_TEXTURE_PROCESSING_NO_LOCS.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
    )
    self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(proceed_button_2=False)
    )

    # Processing states (no locations) for surface texture processing
    for state_name in [
        States.SURFACE_TEXTURE_WITH_MRI_PROCESSING_NO_LOCS.value,
        States.SURFACE_WITH_MRI_PROCESSING_NO_LOCS.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_tab(2))
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(proceed_button_2=True, restart_button_2=False)
        )

    # -------------------------------
    # Labeling States – update the labeling tab (tab index 4)
    for state in [
        States.LABELING_MRI.value,
        States.LABELING_SURFACE.value,
        States.LABELING_SURFACE_TEXTURE.value,
        States.LABELING_SURFACE_WITH_MRI.value,
        States.LABELING_SURFACE_TEXTURE_WITH_MRI.value,
    ]:
        self.state_machine.add_state(State(state))
        self.state_machine[state].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=False, t4=True, t5=True)
        )
        self.state_machine[state].add_callback(lambda: self.switch_tab(4))

    # -------------------------------
    # QC States for Surface – update the surface tab (tab index 2)
    for state in [
        States.QC_SURFACE.value,
        States.QC_SURFACE_TEXTURE.value,
        States.QC_SURFACE_WITH_MRI.value,
    ]:
        self.state_machine.add_state(State(state))
        self.state_machine[state].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
        )
        self.state_machine[state].add_callback(lambda: self.switch_tab(2))
        self.state_machine[state].add_callback(
            lambda: self.update_button_states(proceed_button_2=False, restart_button_2=True)
        )

    # QC States for MRI – update the MRI tab (tab index 3)
    state = States.QC_MRI.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(3))
    self.state_machine[state].add_callback(
        lambda: self.update_button_states(proceed_button_3=False)
    )

    for state in [
        States.SURFACE_TO_MRI_ALIGNMENT.value,
        States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT.value,
    ]:
        self.state_machine.add_state(State(state))
        self.state_machine[state].add_callback(
            lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
        )
        self.state_machine[state].add_callback(lambda: self.switch_tab(3))
        self.state_machine[state].add_callback(
            lambda: self.ui.display_secondary_mesh_checkbox.setChecked(False)
        )

    state = States.QC_SURFACE_TEXTURE_WITH_MRI.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(2))
    self.state_machine[state].add_callback(
        lambda: self.update_button_states(proceed_button_2=False)
    )

    # New Alignment & QC States for Texture with MRI (no locations)
    state = States.SURFACE_TEXTURE_TO_MRI_ALIGNMENT_NO_LOCS.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(3))
    self.state_machine[state].add_callback(
        lambda: self.ui.display_secondary_mesh_checkbox.setChecked(False)
    )

    state = States.QC_SURFACE_TEXTURE_WITH_MRI_NO_LOCS.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(2))
    self.state_machine[state].add_callback(
        lambda: self.update_button_states(proceed_button_2=False)
    )

    state = States.SURFACE_TO_MRI_ALIGNMENT_NO_LOCS.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=False, t3=True, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(3))
    self.state_machine[state].add_callback(
        lambda: self.ui.display_secondary_mesh_checkbox.setChecked(False)
    )

    state = States.QC_SURFACE_WITH_MRI_NO_LOCS.value
    self.state_machine.add_state(State(state))
    self.state_machine[state].add_callback(
        lambda: self.update_tab_states(t0=True, t1=False, t2=True, t3=False, t4=False, t5=True)
    )
    self.state_machine[state].add_callback(lambda: self.switch_tab(2))
    self.state_machine[state].add_callback(
        lambda: self.update_button_states(proceed_button_2=False, restart_button_2=True)
    )
