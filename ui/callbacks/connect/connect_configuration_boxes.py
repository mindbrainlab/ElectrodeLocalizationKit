from config.electrode_detector import DogParameters, HoughParameters
from config.sizes import ElectrodeSizes
from ui.callbacks.display import display_dog, display_hough


def connect_configuration_boxes(self):
    # texture DoG spinbox slot connections
    self.ui.kernel_size_spinbox.valueChanged.connect(lambda: _display_dog(self))
    self.ui.sigma_spinbox.valueChanged.connect(lambda: _display_dog(self))
    self.ui.diff_factor_spinbox.valueChanged.connect(lambda: _display_dog(self))

    # texture Hough spinbox slot connections
    self.ui.param1_spinbox.valueChanged.connect(lambda: _display_hough(self))
    self.ui.param2_spinbox.valueChanged.connect(lambda: _display_hough(self))
    self.ui.min_dist_spinbox.valueChanged.connect(lambda: _display_hough(self))
    self.ui.min_radius_spinbox.valueChanged.connect(lambda: _display_hough(self))
    self.ui.max_radius_spinbox.valueChanged.connect(lambda: _display_hough(self))

    # surface configuration slot connections
    self.ui.sphere_size_spinbox.valueChanged.connect(self.update_surf_config)
    self.ui.flagposts_checkbox.stateChanged.connect(self.update_surf_config)
    self.ui.flagpost_height_spinbox.valueChanged.connect(self.update_surf_config)
    self.ui.flagpost_size_spinbox.valueChanged.connect(self.update_surf_config)

    # mri configuration slot connections
    self.ui.mri_sphere_size_spinbox.valueChanged.connect(self.update_mri_config)
    self.ui.mri_flagposts_checkbox.stateChanged.connect(self.update_mri_config)
    self.ui.mri_flagpost_height_spinbox.valueChanged.connect(self.update_mri_config)
    self.ui.mri_flagpost_size_spinbox.valueChanged.connect(self.update_mri_config)

    # label configuration slot connections
    self.ui.label_sphere_size_spinbox.valueChanged.connect(
        self.update_reference_labeling_config
    )
    self.ui.label_flagposts_checkbox.stateChanged.connect(
        self.update_reference_labeling_config
    )
    self.ui.label_flagpost_height_spinbox.valueChanged.connect(
        self.update_reference_labeling_config
    )
    self.ui.label_flagpost_size_spinbox.valueChanged.connect(
        self.update_reference_labeling_config
    )

    _set_defaults_to_configuration_boxes(self)


def _display_dog(self):
    if self.files["texture"] is not None:
        display_dog(
            self.images,
            self.ui.texture_frame,
            self.ui.photo_label,
            self.electrode_detector,
            self.ui.kernel_size_spinbox.value(),
            self.ui.sigma_spinbox.value(),
            self.ui.diff_factor_spinbox.value(),
        )


def _display_hough(self):
    if self.files["texture"] is not None:
        display_hough(
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


def _set_defaults_to_configuration_boxes(self):
    # texture DoG spinbox default values
    self.ui.kernel_size_spinbox.setValue(DogParameters.KSIZE)
    self.ui.sigma_spinbox.setValue(DogParameters.SIGMA)
    self.ui.diff_factor_spinbox.setValue(DogParameters.FACTOR)

    # texture Hough spinbox default values
    self.ui.param1_spinbox.setValue(HoughParameters.PARAM1)
    self.ui.param2_spinbox.setValue(HoughParameters.PARAM2)
    self.ui.min_dist_spinbox.setValue(HoughParameters.MIN_DISTANCE)
    self.ui.min_radius_spinbox.setValue(HoughParameters.MIN_RADIUS)
    self.ui.max_radius_spinbox.setValue(HoughParameters.MAX_RADIUS)

    # electrode size spinbox default values
    self.ui.sphere_size_spinbox.setValue(ElectrodeSizes.HEADSCAN_ELECTRODE_SIZE)
    self.ui.flagpost_size_spinbox.setValue(ElectrodeSizes.HEADSCAN_FLAGPOST_SIZE)
    self.ui.flagpost_height_spinbox.setValue(ElectrodeSizes.HEADSCAN_FLAGPOST_HEIGHT)

    # mri electrode size spinbox default values
    self.ui.mri_sphere_size_spinbox.setValue(ElectrodeSizes.MRI_ELECTRODE_SIZE)
    self.ui.mri_flagpost_size_spinbox.setValue(ElectrodeSizes.MRI_FLAGPOST_SIZE)
    self.ui.mri_flagpost_height_spinbox.setValue(ElectrodeSizes.MRI_FLAGPOST_HEIGHT)

    # label electrode size spinbox default values
    self.ui.label_sphere_size_spinbox.setValue(ElectrodeSizes.LABEL_ELECTRODE_SIZE)
    self.ui.label_flagpost_size_spinbox.setValue(ElectrodeSizes.LABEL_FLAGPOST_SIZE)
    self.ui.label_flagpost_height_spinbox.setValue(ElectrodeSizes.LABEL_FLAGPOST_HEIGHT)
