from ui.callbacks.refresh_views import refresh_count_indicators


def connect_model(self):
    self.model.dataChanged.connect(
        lambda: refresh_count_indicators(
            self.model,
            self.ui.measured_electrodes_label,
            self.ui.labeled_electrodes_label,
            self.ui.reference_electrodes_label,
        )
    )
    self.model.rowsInserted.connect(
        lambda: refresh_count_indicators(
            self.model,
            self.ui.measured_electrodes_label,
            self.ui.labeled_electrodes_label,
            self.ui.reference_electrodes_label,
        )
    )
    self.model.rowsRemoved.connect(
        lambda: refresh_count_indicators(
            self.model,
            self.ui.measured_electrodes_label,
            self.ui.labeled_electrodes_label,
            self.ui.reference_electrodes_label,
        )
    )
