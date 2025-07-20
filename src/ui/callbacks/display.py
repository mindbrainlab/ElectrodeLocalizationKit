from view.surface_view import SurfaceView
from processing_models.electrode_detector import DogHoughElectrodeDetector
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel

from config.electrode_detector import DogParameters, HoughParameters


def display_surface(surface_view: SurfaceView | None):
    if surface_view is not None:
        frame_size = surface_view.frame.size()
        surface_view.resize_view(frame_size.width(), frame_size.height())

        surface_view.show()


def set_surface_alpha(surface_view: SurfaceView | None, alpha: float, actor_index: int = 0):
    if surface_view is not None:
        surface_view.update_surf_alpha(alpha, actor_index)


def display_dog(
    images: dict,
    frame: QFrame,
    image_label: QLabel,
    dog_hough_detector: DogHoughElectrodeDetector,
    ksize: int = DogParameters.KSIZE,
    sigma: float = DogParameters.SIGMA,
    F: float = DogParameters.FACTOR,
):
    dog = dog_hough_detector.get_difference_of_gaussians(ksize=ksize, sigma=sigma, F=F)

    if dog is None:
        return

    images["dog"] = QImage(
        dog.data,
        dog.shape[1],
        dog.shape[0],
        QImage.Format.Format_Grayscale8,
    ).rgbSwapped()

    label_size = frame.size()
    images["dog"] = images["dog"].scaled(
        label_size.width(),
        label_size.height(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )

    image_label.setPixmap(QPixmap.fromImage(images["dog"]))


def display_hough(
    images: dict,
    frame: QFrame,
    image_label: QLabel,
    dog_hough_detector: DogHoughElectrodeDetector,
    param1: float = HoughParameters.PARAM1,
    param2: float = HoughParameters.PARAM2,
    min_distance: int = HoughParameters.MIN_DISTANCE,
    min_radius: int = HoughParameters.MIN_RADIUS,
    max_radius: int = HoughParameters.MAX_RADIUS,
):
    hough = dog_hough_detector.get_hough_circles(
        param1=param1,
        param2=param2,
        min_distance_between_circles=min_distance,
        min_radius=min_radius,
        max_radius=max_radius,
    )

    if hough is None:
        return

    images["hough"] = QImage(
        hough.data,
        hough.shape[1],
        hough.shape[0],
        QImage.Format.Format_RGB888,
    ).rgbSwapped()

    label_size = frame.size()
    images["hough"] = images["hough"].scaled(
        label_size.width(),
        label_size.height(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.FastTransformation,
    )

    image_label.setPixmap(QPixmap.fromImage(images["hough"]))
