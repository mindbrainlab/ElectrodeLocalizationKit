from ui.callbacks.display import set_surface_alpha


def connect_alpha_sliders(self):
    self.ui.head_alpha_slider.valueChanged.connect(
        lambda: set_surface_alpha(self.views["scan"], self.ui.head_alpha_slider.value() / 100)
    )
    self.ui.mri_alpha_slider.valueChanged.connect(
        lambda: set_surface_alpha(self.views["mri"], self.ui.mri_alpha_slider.value() / 100)
    )
    self.ui.mri_head_alpha_slider.valueChanged.connect(
        lambda: set_surface_alpha(
            self.views["mri"],
            self.ui.mri_head_alpha_slider.value() / 100,
            actor_index=1,
        )
    )
