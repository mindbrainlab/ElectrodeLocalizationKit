from abc import ABC, abstractmethod
import numpy as np
import vedo as vd
from utils.mesh import align_with_landmarks, arrayFromVTKMatrix
from data_models.electrode import Electrode


class BaseSurfaceRegistrator(ABC):
    @abstractmethod
    def register(self, source_mesh: vd.Mesh):
        pass

    @abstractmethod
    def undo(self):
        pass


class LandmarkSurfaceRegistrator(BaseSurfaceRegistrator):
    def __init__(self):
        self.source_mesh = None
        self.source_landmarks = None
        self.target_landmarks = None

        self._transform_matrix = None
        self._inverse_transform = None

    def set_mesh(self, source_mesh: vd.Mesh):
        self.source_mesh = source_mesh

    def set_landmarks(self, source_landmarks: list[Electrode], target_landmarks: list[Electrode]):
        self.source_landmarks = source_landmarks
        self.target_landmarks = target_landmarks

    def register(self) -> np.ndarray:
        lmt = align_with_landmarks(
            self.source_mesh,
            self.source_landmarks,
            self.target_landmarks,
            rigid=False,
            affine=False,
            least_squares=False,
        )

        self._transform_matrix = arrayFromVTKMatrix(lmt.GetMatrix())
        return self._transform_matrix

    def undo(self) -> np.ndarray | None:
        if self.source_mesh is not None and self._transform_matrix is not None:
            self._inverse_transform_matrix = np.linalg.inv(self._transform_matrix)
            self.source_mesh.applyTransform(self._inverse_transform_matrix)
        else:
            self._inverse_transform_matrix = None
        return self._inverse_transform_matrix
