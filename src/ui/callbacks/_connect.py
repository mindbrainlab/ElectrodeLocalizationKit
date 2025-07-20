from fileio.scan import load_surface, load_texture
from fileio.mri import load_mri
from fileio.locations import load_locations, save_locations_to_file
from processing_handlers.texture_processing import detect_electrodes
from config.electrode_detector import DogParameters, HoughParameters
from config.sizes import ElectrodeSizes

from callbacks.display import (
    display_surface,
    set_surface_alpha,
)


def connect_model(self):
    self.model.dataChanged.connect(self.refresh_count_indicators)
    self.model.rowsInserted.connect(self.refresh_count_indicators)
    self.model.rowsRemoved.connect(self.refresh_count_indicators)


def connect_fileio_buttons(self):
    self.ui.load_surface_button.clicked.connect(
        lambda: load_surface(
            self.files,
            self.views,
            self.headmodels,
            [
                ("scan", self.ui.headmodel_frame),
                ("labeling_main", self.ui.labeling_main_frame),
            ],
            self.model,
        )
    )

    self.ui.load_texture_button.clicked.connect(
        lambda: load_texture(
            self.files,
            self.views,
            self.headmodels,
            [
                ("scan", self.ui.headmodel_frame),
                ("labeling_main", self.ui.labeling_main_frame),
            ],
            self.model,
            self.electrode_detector,
        )
    )
    self.ui.load_mri_button.clicked.connect(
        lambda: load_mri(
            self.files,
            self.views,
            self.headmodels,
            [("mri", self.ui.mri_frame)],
            self.model,
        )
    )
    self.ui.load_locations_button.clicked.connect(
        lambda: load_locations(
            self.files,
            self.views,
            [("labeling_reference", self.ui.labeling_reference_frame)],
            self.model,
        )
    )

    self.ui.export_locations_button.clicked.connect(lambda: save_locations_to_file(self.model))


def connect_texture_buttons(self):
    self.ui.display_dog_button.clicked.connect(self.display_dog)
    self.ui.display_hough_button.clicked.connect(self.display_hough)
    # texture detect electrodes button slot connection
    self.ui.compute_electrodes_button.clicked.connect(
        lambda: detect_electrodes(
            self.headmodels["scan"],  # type: ignore
            self.electrode_detector,
            self.model,
        )
    )


def connect_display_surface_buttons(self):
    self.ui.display_head_button.clicked.connect(lambda: display_surface(self.views["scan"]))
    self.ui.display_mri_button.clicked.connect(lambda: display_surface(self.views["mri"]))
    self.ui.label_display_button.clicked.connect(
        lambda: display_surface(self.views["labeling_main"])
    )


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


def connect_configuration_boxes(self):
    # texture DoG spinbox slot connections
    self.ui.kernel_size_spinbox.valueChanged.connect(self.display_dog)
    self.ui.sigma_spinbox.valueChanged.connect(self.display_dog)
    self.ui.diff_factor_spinbox.valueChanged.connect(self.display_dog)

    # texture Hough spinbox slot connections
    self.ui.param1_spinbox.valueChanged.connect(self.display_hough)
    self.ui.param2_spinbox.valueChanged.connect(self.display_hough)
    self.ui.min_dist_spinbox.valueChanged.connect(self.display_hough)
    self.ui.min_radius_spinbox.valueChanged.connect(self.display_hough)
    self.ui.max_radius_spinbox.valueChanged.connect(self.display_hough)

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
    self.ui.label_sphere_size_spinbox.valueChanged.connect(self.update_reference_labeling_config)
    self.ui.label_flagposts_checkbox.stateChanged.connect(self.update_reference_labeling_config)
    self.ui.label_flagpost_height_spinbox.valueChanged.connect(
        self.update_reference_labeling_config
    )
    self.ui.label_flagpost_size_spinbox.valueChanged.connect(self.update_reference_labeling_config)


def set_defaults_to_configuration_boxes(self):
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
