from PyQt6.QtWidgets import QMessageBox


def throw_fiducials_warning():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("The fiducials in the scan and MRI do not match.")
    msg.setInformativeText(
        "Please ensure that the same set of fiducials are present in both modalities."
    )
    msg.setWindowTitle("Fiducials Mismatch")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


def throw_electrode_registration_warning():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Not enough electrodes labeled.")
    msg.setInformativeText(
        "Please ensure at least three electrodes are labeled before registration."
    )
    msg.setWindowTitle("Electrode Registration Incomplete")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
