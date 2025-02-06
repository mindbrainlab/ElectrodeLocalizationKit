from config.mappings import ModalitiesMapping
from .state_machine import States, State


def initialize_states(self):
    # initial states
    state_name = States.INITIAL.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=True,
            load_texture_button=False,
            load_mri_button=True,
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
    self.state_machine[state_name].add_callback(lambda: self.set_data_containers())
    self.state_machine[state_name].add_callback(lambda: self.model.clear())

    state_name = States.LOCATIONS_LOADED.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=True,
            load_texture_button=False,
            load_mri_button=True,
            load_locations_button=True,
        )
    )

    state_name = States.SURFACE_READY.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_texture_button=True,
        )
    )

    state_name = States.SURFACE_TEXTURE_READY.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=False,
        )
    )

    state_name = States.MRI_READY.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_mri_button=False,
        )
    )

    state_name = States.SURFACE_MRI_READY.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_surface_button=False,
            load_mri_button=False,
            load_texture_button=True,
        )
    )

    state_name = States.SURFACE_TEXTURE_MRI_READY.value
    self.state_machine.add_state(State(state_name))
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            load_texture_button=True,
        )
    )

    # processing mode states
    for state_name in [
        States.TEXTURE_PROCESSING_DOG.value,
        States.TEXTURE_WITH_MRI_PROCESSING_DOG.value,
    ]:
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
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(
                proceed_button_1=False,
            )
        )
        self.state_machine[state_name].add_callback(lambda: self.switch_tab(1))
        self.state_machine[state_name].add_callback(
            lambda: self.model.clear_electrodes_by_modality(ModalitiesMapping.HEADSCAN)
        )

    for state_name in [
        States.TEXTURE_PROCESSING_HOUGH.value,
        States.TEXTURE_WITH_MRI_PROCESSING_HOUGH.value,
    ]:
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
        # self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(1))
        self.state_machine[state_name].add_callback(lambda: self.switch_texture_tab(0))

    for state_name in [
        States.TEXTURE_HOUGH_COMPUTED.value,
        States.TEXTURE_WITH_MRI_HOUGH_COMPUTED.value,
    ]:
        self.state_machine.add_state(State(state_name))
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(
                proceed_button_1=True,
            )
        )

    for state_name in [
        States.SURFACE_PROCESSING.value,
        States.SURFACE_TEXTURE_PROCESSING.value,
        States.SURFACE_WITH_MRI_PROCESSING.value,
        States.SURFACE_TEXTURE_WITH_MRI_PROCESSING.value,
    ]:
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
        self.state_machine[state_name].add_callback(
            lambda: self.update_button_states(
                restart_button_2=False,
            )
        )

    state_name = States.MRI_PROCESSING.value
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

    for state_name in [
        States.LABELING_SURFACE.value,
        States.LABELING_MRI.value,
        States.LABELING_SURFACE_WITH_MRI.value,
    ]:
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

    state_name = States.SURFACE_TO_MRI_ALIGNMENT.value
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

    state_name = States.QC_SURFACE.value
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
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            proceed_button_2=False,
        )
    )

    state_name = States.QC_MRI.value
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
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            proceed_button_3=False,
        )
    )

    state_name = States.QC_SURFACE_WITH_MRI.value
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
    self.state_machine[state_name].add_callback(
        lambda: self.update_button_states(
            proceed_button_2=False,
        )
    )
