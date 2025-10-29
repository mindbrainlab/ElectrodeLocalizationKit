import os
import logging
import numpy as np
import pandas as pd

from ui.pyloc_main_window import Ui_ELK
from data_models.cap_model import CapModel
from data_models.electrode import Electrode
from data_models.head_models import HeadScan
from config.logger_config import setup_logger
from processing_models.mesh import MeshLoader
from view.interactive_surface_view import InteractiveSurfaceView
from processing_models.electrode import (
    DetectionMethod,
    ElectrodeMapper,
    ProcessingParams,
    ViewType,
    ViewLoader,
)


setup_logger(logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = "./temp"
VIEWS_PATH = "./temp"
FIDUCIALS_PATH = "./temp/fiducials.csv"
ELECTRODES_PATH = "./temp/electrodes.csv"

FIDUCIALS_REQUIRED = {"NAS", "INI", "LPA", "RPA", "VTX"}
VIEW_TYPES = [
    ViewType.FRONT,
    ViewType.BACK,
    ViewType.TOP,
    ViewType.RIGHT,
    ViewType.LEFT,
    ViewType.FRONT_TOP,
    ViewType.BACK_TOP,
    ViewType.FRONT_RIGHT,
    ViewType.FRONT_LEFT,
    ViewType.BACK_RIGHT,
    ViewType.BACK_LEFT,
    ViewType.TOP_RIGHT,
    ViewType.TOP_LEFT,
]
DETECTION_METHODS = [
    DetectionMethod.TRADITIONAL,
    DetectionMethod.FRST,
]


def process_mesh(
    view: InteractiveSurfaceView,
    headmodel: HeadScan,
    model: CapModel,
    loaders: dict[str, MeshLoader | ViewLoader],
    ui: Ui_ELK = None,
):
    fiducials = model.get_fiducials([headmodel.modality])

    # Save fiducials to file
    os.makedirs(TEMP_DIR, exist_ok=True)
    with open(FIDUCIALS_PATH, "w", encoding="utf-8") as f:
        for fid in fiducials:
            if (
                fid is not None
                and fid.label is not None
                and fid.label in FIDUCIALS_REQUIRED
                and fid.coordinates is not None
            ):
                f.write(
                    f"{fid.label},{fid.coordinates[0]},{fid.coordinates[1]},{fid.coordinates[2]}\n"
                )
        logger.info(f"Fiducials saved to {FIDUCIALS_PATH}")

    # Process mesh
    mesh_loader = MeshLoader(headmodel.surface_file, headmodel.texture_file, FIDUCIALS_PATH)
    loaders["mesh"] = mesh_loader
    mesh_loader.clean_data(x_margin=0.5, y_top_margin=0.25, y_bottom_margin=1.0, z_margin=0.25)
    mesh_loader.extract_cap_data(margin=0.0)
    mesh_loader.capture_data(VIEWS_PATH)

    # Transform fiducials back
    transformed_fiducials = pd.DataFrame(
        transform_points(
            mesh_loader.fiducials.to_numpy(),
            mesh_loader.aligner.source_origin,
            mesh_loader.aligner.rotation_matrix,
            inverse=True,
        ),
        index=mesh_loader.fiducials.index,
        columns=mesh_loader.fiducials.columns,
    )

    # Update fiducial locations
    for i in range(len(fiducials)):
        if fiducials[i].label is not None and fiducials[i].label in transformed_fiducials.index:
            point = transformed_fiducials.loc[fiducials[i].label].values
            fiducials[i].coordinates = point

    # Rerender
    ui and ui.detect_button.setEnabled(True)
    view.render_electrodes()


def detect_electrodes(
    view: InteractiveSurfaceView,
    headmodel: HeadScan,
    model: CapModel,
    loaders: dict[str, MeshLoader | ViewLoader],
):
    mesh_loader = loaders["mesh"]
    view_loader = ViewLoader(VIEWS_PATH, ProcessingParams())
    loaders["view"] = view_loader

    # Detect markers and electrodes (in parallel)
    view_loader.detect_markers_and_electrodes(VIEW_TYPES, DETECTION_METHODS)

    # Label markers
    view_loader.label_markers(VIEW_TYPES)

    # Map electrodes
    mapper = ElectrodeMapper(
        mesh_loader.mesh_cleaned,
        mesh_loader.mesh_extracted,
        mesh_loader.fiducials,
        mesh_loader.aligner.origin,
    )
    mapper.map_electrodes_to_3d(view_loader.detected, view_loader.metadata)

    # Transform electrodes back
    transformed_electrodes = mapper.electrodes.copy()
    transformed_electrodes[:, (2, 3, 4)] = transform_points(
        transformed_electrodes[:, (2, 3, 4)],
        mesh_loader.aligner.source_origin,
        mesh_loader.aligner.rotation_matrix,
        inverse=True,
    )
    mapper.save(ELECTRODES_PATH, transformed_electrodes)
    electrodes = pd.DataFrame(
        transformed_electrodes[:, (2, 3, 4, 5)],
        columns=["x", "y", "z", "label"],
        index=[method.value for method in mapper.electrodes[:, 1]],
    )

    # Project electrodes on map
    for _, row in electrodes.iterrows():
        point = (row["x"], row["y"], row["z"])
        label = row["label"] if pd.notna(row["label"]) else "None"
        labeled = pd.notna(row["label"])
        model.insert_electrode(
            Electrode(point, modality=headmodel.modality, label=label, labeled=labeled)
        )
    view.render_electrodes()


def transform_points(points, origin, rotation_matrix, inverse=False):
    """
    Transform 3D points between coordinate systems.
    X' = (X - O) @ R^T -> X = X' @ R + O
    Rotation matrix: R^T @ R = R @ R^T = I -> R^-1 = R^T
    """
    points = np.asarray(points.copy())
    origin = np.asarray(origin.copy())
    R = np.asarray(rotation_matrix.copy())

    if not inverse:
        transformed = (points - origin) @ R.T
    else:
        transformed = points @ R + origin

    return transformed
