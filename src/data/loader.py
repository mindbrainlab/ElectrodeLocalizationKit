import nibabel as nib
import numpy as np
import pandas as pd
import vedo as vd

from config.mappings import ElectrodesFileMapping, ModalitiesMapping
from data_models.electrode import Electrode


def load_head_surface_mesh_from_file(filename: str) -> vd.Mesh:
    """Loads a head surface mesh from a file."""
    return vd.Mesh(filename)


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
    elif filename.endswith(".csv"):
        df = pd.read_csv(filename)
    elif filename.endswith(".tsv"):
        df = pd.read_csv(filename, sep="\t")
    else:
        raise ValueError(
            "Unsupported file format - Currently only .ced/.csv/.tsv files are supported."
        )

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
    print(f"Loaded {len(electrodes)} electrodes from {filename}")
    return electrodes
