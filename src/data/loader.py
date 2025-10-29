from data_models.electrode import Electrode
from config.mappings import ElectrodesFileMapping, ModalitiesMapping
import pandas as pd
import numpy as np

import vedo as vd
import nibabel as nib

from processing_models.mesh.mesh_loader import MeshLoader


def load_head_surface_mesh_from_file(surface_file: str, texture_file: str = None) -> vd.Mesh:
    """Loads a head surface mesh from a file."""
    mesh_loader = MeshLoader(surface_file, texture_file)
    return mesh_loader.mesh_preprocessed.clone()


def load_mri_surface_mesh_from_file(filename: str) -> vd.Mesh:
    """Loads an MRI surface mesh from a file."""
    img = nib.load(filename)  # type: ignore
    verts = img.darrays[0].data  # type: ignore
    cells = img.darrays[1].data  # type: ignore
    return vd.Mesh([verts, cells])


def load_electrodes_from_file(filename: str) -> list[Electrode]:
    """Loads electrodes from a file."""
    if filename.endswith(".ced"):
        df = pd.read_csv(filename, sep="\t")
        # df = df[df.type == "EEG"]
    else:
        raise ValueError("Unsupported file format - Currently only .ced files are supported.")

    electrodes = []
    for _, row in df.iterrows():
        electrodes.append(
            Electrode(
                np.array(
                    [
                        float(row[ElectrodesFileMapping.CED_X]),
                        float(row[ElectrodesFileMapping.CED_Y]),
                        float(row[ElectrodesFileMapping.CED_Z]),
                    ]
                ),
                modality=ModalitiesMapping.REFERENCE,
                label=row[ElectrodesFileMapping.CED_LABEL],
                labeled=True,
            )
        )
    return electrodes
