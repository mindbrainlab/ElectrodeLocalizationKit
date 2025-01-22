from ui.callbacks.display import display_dog, display_hough
from processing_handlers.texture_processing import detect_electrodes


def connect_texture_buttons(self):
    self.ui.display_dog_button.clicked.connect(
        lambda: display_dog(
            self.images,
            self.ui.texture_frame,
            self.ui.photo_label,
            self.electrode_detector,
            self.ui.kernel_size_spinbox.value(),
            self.ui.sigma_spinbox.value(),
            self.ui.diff_factor_spinbox.value(),
        )
    )
    self.ui.display_hough_button.clicked.connect(
        lambda: display_hough(
            self.images,
            self.ui.texture_frame,
            self.ui.photo_label,
            self.electrode_detector,
            self.ui.param1_spinbox.value(),
            self.ui.param2_spinbox.value(),
            self.ui.min_dist_spinbox.value(),
            self.ui.min_radius_spinbox.value(),
            self.ui.max_radius_spinbox.value(),
        )
    )

    self.ui.proceed_button_1.clicked.connect(
        lambda: detect_electrodes(
            self.headmodels["scan"],
            self.electrode_detector,
            self.model,
            self.ui,
        )
    )
