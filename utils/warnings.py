from PyQt6.QtWidgets import QMessageBox


def throw_fiducials_warning():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText("The fiducials in the scan and MRI do not match.")
    msg.setInformativeText(
        "Please ensure that the same set of fiducials are present in both modalities."
    )
    msg.setWindowTitle("Fiducials Mismatch")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
