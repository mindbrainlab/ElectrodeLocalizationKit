from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
)

import logging

logger = logging.getLogger(__name__)


class LabelingDialog(QDialog):
    def __init__(self, possible_labels: list[str] | None = None):
        super().__init__()

        self.setWindowTitle("Select Electrode")
        self.setFixedSize(300, 150)

        # Variable to store the label
        self.electrode_label = ""

        # Create layout
        layout = QVBoxLayout()

        self.label = QLabel("Label Electrode", self)
        layout.addWidget(self.label)

        # If possible_labels is provided, use QComboBox, otherwise use QLineEdit
        if possible_labels:
            self.combo_box = QComboBox(self)
            self.combo_box.addItems(possible_labels)
            layout.addWidget(self.combo_box)
            self.combo_box.setFocus()
        else:
            self.line_edit = QLineEdit(self)
            layout.addWidget(self.line_edit)

        # Create buttons
        self.select_button = QPushButton("Select", self)
        self.select_button.clicked.connect(self.select_electrode)
        layout.addWidget(self.select_button)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)  # Close dialog
        layout.addWidget(self.cancel_button)

        # Set the layout to the dialog
        self.setLayout(layout)

        # Connect the Enter key if QLineEdit is used
        if not possible_labels:
            self.line_edit.returnPressed.connect(self.select_electrode)

    def select_electrode(self):
        # Store the selected/entered electrode label
        if hasattr(self, "combo_box"):  # If we have a combo box
            self.electrode_label = self.combo_box.currentText()
        else:  # If we have a line edit
            self.electrode_label = self.line_edit.text()

        logger.info(
            f"Selected Electrode: {self.electrode_label}"
        )  # Placeholder for actual selection logic
        self.accept()  # Close the dialog with accepted status

    def get_electrode_label(self):
        return self.electrode_label
