from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)


class LabelingDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select Electrode")
        self.setFixedSize(300, 150)

        # Variable to store the label
        self.electrode_label = ""

        # Create layout
        layout = QVBoxLayout()

        # Create label and line edit
        self.label = QLabel("Label Electrode", self)
        layout.addWidget(self.label)

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

        # Connect the Enter key
        self.line_edit.returnPressed.connect(self.select_electrode)

    def select_electrode(self):
        # Store the entered electrode label
        self.electrode_label = self.line_edit.text()
        print(
            f"Selected Electrode: {self.electrode_label}"
        )  # Placeholder for actual selection logic
        self.accept()  # Close the dialog with accepted status

    def get_electrode_label(self):
        return self.electrode_label
