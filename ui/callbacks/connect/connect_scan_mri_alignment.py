from processing_handlers.scan_mri_alignment import (
    align_scan_to_mri,
    undo_scan2mri_transformation,
    project_electrodes_to_mri,
    display_secondary_mesh,
)


def connect_scan_mri_alignment_buttons(self):
    self.ui.align_scan_button.clicked.connect(
        lambda: align_scan_to_mri(
            self.views,
            self.headmodels,
            self.model,
            self.surface_registrator,
            self.ui,
        )
    )

    self.ui.project_electrodes_button.clicked.connect(
        lambda: project_electrodes_to_mri(self.headmodels, self.model, self.views)
    )


def connect_display_secondary_mesh_checkbox(self):
    self.ui.display_secondary_mesh_checkbox.stateChanged.connect(
        lambda: display_secondary_mesh(
            self.views, self.headmodels, self.ui.display_secondary_mesh_checkbox
        )
    )
