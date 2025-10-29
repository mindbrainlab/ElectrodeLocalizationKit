from processing_handlers.detection_processing import detect_electrodes, process_mesh


def connect_detection_buttons(self):
    self.ui.process_button.clicked.connect(
        lambda: process_mesh(
            self.views["scan"],
            self.headmodels["scan"],
            self.model,
            self.loaders,
            self.ui,
        )
    )
    self.ui.detect_button.clicked.connect(
        lambda: detect_electrodes(
            self.views["scan"],
            self.headmodels["scan"],
            self.model,
            self.loaders,
        )
    )
