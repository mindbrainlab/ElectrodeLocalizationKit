from ui.callbacks.fileio import (
    load_surface,
    load_texture,
    load_mri,
    load_locations,
    save_locations_to_file,
)


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
            self.ui,
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
            self.ui,
        )
    )
    self.ui.load_mri_button.clicked.connect(
        lambda: load_mri(
            self.files,
            self.views,
            self.headmodels,
            [("mri", self.ui.mri_frame)],
            self.model,
            self.ui,
        )
    )
    self.ui.load_locations_button.clicked.connect(
        lambda: load_locations(
            self.files,
            self.views,
            [("labeling_reference", self.ui.labeling_reference_frame)],
            self.model,
            self.ui,
        )
    )

    self.ui.export_locations_button.clicked.connect(
        lambda: save_locations_to_file(self.model, self.ui)
    )
