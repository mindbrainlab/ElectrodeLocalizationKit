from abc import ABC, abstractmethod
import numpy as np
import cv2 as cv
import vedo as vd

from model.electrode import Electrode

from utils.texture import compute_difference_of_gaussians, compute_hough_circles

from config.electrode_detector import DogParameters, HoughParameters
from config.colors import HOUGH_CIRCLES_COLOR
from config.mappings import ModalitiesMapping


class BaseElectrodeDetector(ABC):

    @abstractmethod
    def apply_texture(self, texture_file: str):
        pass

    @abstractmethod
    def detect(self) -> list[Electrode]:
        pass


class DogHoughElectrodeDetector(BaseElectrodeDetector):
    def __init__(self):
        self.dog = None
        self.circles = None
        self.texture = None
        self.electrodes = []

        self.modality = ModalitiesMapping.HEADSCAN

    def apply_texture(self, texture_file: str):
        self._texture_file = texture_file
        self.texture = cv.imread(texture_file)

    def detect(self, mesh: vd.Mesh) -> list[Electrode]:
        if self.texture is None:
            return []

        for circle in self.circles[0, :]:  # type: ignore
            vertex = self._get_vertex_from_pixels(
                (circle[0], circle[1]), mesh, self.texture.shape[0:2]
            )
            self.electrodes.append(
                Electrode(vertex, modality=self.modality, label="None")
            )

        electrodes_to_remove = self._get_electrodes_too_close_together()

        self.electrodes = [
            electrode
            for i, electrode in enumerate(self.electrodes)
            if i not in electrodes_to_remove
        ]

        return self.electrodes

    def get_difference_of_gaussians(
        self,
        ksize: int = DogParameters.KSIZE,
        sigma: float = DogParameters.SIGMA,
        F: float = DogParameters.FACTOR,
        threshold_level: int = DogParameters.THRESHOLD_LEVEL,
    ) -> np.ndarray | None:

        if self.texture is None:
            return None

        self.dog = compute_difference_of_gaussians(
            image=self.texture,
            ksize=ksize,
            sigma=sigma,
            F=F,
            threshold_level=threshold_level,
        )
        return self.dog

    def get_hough_circles(
        self,
        param1: float = HoughParameters.PARAM1,
        param2: float = HoughParameters.PARAM2,
        min_distance_between_circles: int = HoughParameters.MIN_DISTANCE,
        min_radius: int = HoughParameters.MIN_RADIUS,
        max_radius: int = HoughParameters.MAX_RADIUS,
    ) -> np.ndarray | None:
        if self.dog is None:
            raise Exception(
                "No DoG image available. Please run diff_of_gaussians() first."
            )

        if self.texture is None:
            return None

        circles_image, self.circles = compute_hough_circles(
            self.texture,
            self.dog,
            param1,
            param2,
            min_distance_between_circles,
            min_radius,
            max_radius,
            HOUGH_CIRCLES_COLOR,
        )
        return circles_image

    def _get_electrodes_too_close_together(self, min_distance: float = 0.075) -> list:
        electrodes_to_remove = []
        dist_matrix = np.zeros((len(self.electrodes), len(self.electrodes)))
        for i, electrode_a in enumerate(self.electrodes):
            for j, electrode_b in enumerate(self.electrodes):
                if i != j:
                    dist = np.linalg.norm(
                        electrode_a.coordinates - electrode_b.coordinates
                    )
                    if dist < min_distance:
                        electrodes_to_remove.append(i)
                        electrodes_to_remove.append(j)

        return electrodes_to_remove

    def _get_vertex_from_pixels(
        self, pixels: tuple[float, float], mesh: vd.Mesh, image_size
    ) -> np.ndarray:
        # Helper function to get the vertex from the mesh that corresponds to
        # the pixel coordinates
        #
        # Written by: Aleksij Kraljic, October 29, 2023

        vertices = mesh.points()

        # extract the uv coordinates from the mesh
        uv = mesh.pointdata["material_0"]

        # convert pixels to uv coordinates
        uv_image = [
            (pixels[0] + 0.5) / image_size[0],
            1 - (pixels[1] + 0.5) / image_size[1],
        ]

        # find index of closest point in uv with uv_image
        uv_idx = np.argmin(np.linalg.norm(uv - uv_image, axis=1))  # type: ignore

        vertex = vertices[uv_idx]  # type: ignore

        return vertex
