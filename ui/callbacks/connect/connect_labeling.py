from ui.callbacks.labeling import (
    register_reference_electrodes_to_measured,
    undo_labeling,
    align_reference_electrodes_to_measured,
    autolabel_measured_electrodes,
    visualize_labeling_correspondence,
    label_corresponding_electrodes,
    interpolate_missing_electrodes,
)


def connect_labeling_buttons(self):
    self.ui.label_register_button.clicked.connect(
        lambda: register_reference_electrodes_to_measured(
            self.views,
            self.status,
            self.model,
            self.electrode_registrator,
        )
    )
    self.ui.label_align_button.clicked.connect(
        lambda: align_reference_electrodes_to_measured(
            self.model,
            self.views,
            self.status,
            self.electrode_aligner,
        )
    )

    self.ui.label_autolabel_button.clicked.connect(
        lambda: autolabel_measured_electrodes(
            self.model, self.views, self.status, self.electrode_aligner
        )
    )

    self.ui.label_label_correspondence_button.clicked.connect(
        lambda: label_corresponding_electrodes(
            self.model,
            self.views,
            self.status,
            self.electrode_aligner,
        )
    )

    self.ui.correspondence_slider.valueChanged.connect(
        lambda: visualize_labeling_correspondence(
            self.model,
            self.views,
            self.ui.correspondence_slider,
            self.ui.correspondence_slider_label,
        )
    )
    self.ui.label_revert_button.clicked.connect(
        lambda: undo_labeling(
            self.status,
            self.electrode_registrator,
        )
    )

    self.ui.label_interpolate_button.clicked.connect(
        lambda: interpolate_missing_electrodes(self.model)
    )
