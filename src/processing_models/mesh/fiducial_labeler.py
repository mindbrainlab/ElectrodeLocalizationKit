import logging

from dataclasses import dataclass
from typing import List, Optional, Tuple
from vedo import Plotter, Sphere, settings

from .mesh_loader import MeshLoader


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass
class FiducialInfo:
    code: str
    name: str
    color: str


class FiducialLabeler:
    def __init__(self, mesh_path: str, texture_path: str) -> None:
        """
        Interactive tool for labeling anatomical fiducials on a 3D head mesh.
        """

        # Define standard fiducial labels
        self.fiducial_info: List[FiducialInfo] = [
            FiducialInfo("NAS", "Nasion", "red"),
            FiducialInfo("LPA", "Left Pre-Auricular", "blue"),
            FiducialInfo("RPA", "Right Pre-Auricular", "green"),
            FiducialInfo("LHJ", "Left Helix-Tragus Junction", "cyan"),
            FiducialInfo("RHJ", "Right Helix-Tragus Junction", "magenta"),
            FiducialInfo("INI", "Inion", "yellow"),
            FiducialInfo("VTX", "Vertex (Cz approx.)", "orange"),
        ]
        self._current_index: int = 0

        # Initialize mesh loader
        self.mesh_loader = MeshLoader(mesh_path, texture_path)
        self.mesh = self.mesh_loader.mesh

        # Initialize fiducials storage (None until picked)
        self.fiducials: List[Optional[Tuple[str, float, float, float]]] = [
            None for _ in self.fiducial_info
        ]

        # Initialize plotter
        self.plotter = Plotter(title="Fiducial Labeling Tool", size=(1200, 800))

    def _log_fiducial(self) -> None:
        """
        Log which fiducial the user should pick next.
        """
        fiducial = self.fiducial_info[self._current_index]
        logging.info(f"Pick: {fiducial.name} ({fiducial.code})")

    def _on_key_press(self, event) -> None:
        """
        Handle keyboard input events.
        - Press 'q' to quit and print fiducials.
        """
        if event.keypress == "q" or event.keypress == "s":
            logging.info(f"Final fiducials:\n{self.fiducials}")
            logging.info("Exiting Fiducial Labeling Tool...")
            self.plotter.close()

    def _on_middle_click(self, event) -> None:
        """
        Handle middle mouse button clicks to place fiducials.
        """
        fiducial = self.fiducial_info[self._current_index]
        pos = tuple(map(float, event.picked3d))

        logging.info(f"Picked {fiducial.name} ({fiducial.code}) at {pos}")

        # Store fiducial
        self.fiducials[self._current_index] = (fiducial.code, *pos)

        # Move to next fiducial and log instruction
        self._current_index = (self._current_index + 1) % len(self.fiducial_info)
        self._log_fiducial()

        # Place a marker sphere
        self.plotter.add(Sphere(pos=pos, r=2.5, c=fiducial.color))

    def run(self) -> None:
        """
        Start the interactive labeling tool.
        """
        logging.info("Starting Fiducial Labeling Tool...")
        if self.mesh:
            self.plotter.add(self.mesh)

        # Register event callbacks
        self.plotter.add_callback("KeyPress", self._on_key_press)
        self.plotter.add_callback("MiddleButtonPress", self._on_middle_click)

        # Log instruction before first click
        self._log_fiducial()

        # Show interactive window
        self.plotter.show()

    def save(self, file_path: str) -> None:
        """
        Save labeled fiducials to a CSV file.
        Format: CODE,x,y,z
        """
        if self.fiducials is None or any(fid is None for fid in self.fiducials):
            logging.warning("Not all fiducials are labeled.")
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for fid in self.fiducials:
                    if fid is not None:
                        f.write(f"{fid[0]},{fid[1]},{fid[2]},{fid[3]}\n")
            logging.info(f"Fiducials saved to {file_path}")
        except OSError as e:
            logging.error(f"Failed to save fiducials: {e}")
