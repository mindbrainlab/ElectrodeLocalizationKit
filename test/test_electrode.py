from model.electrode import Electrode
import numpy as np


def test_electrode():
    coordinates = np.array([0, 0, 0])
    electrode = Electrode(coordinates, "scan")
    assert electrode.coordinates[0] == coordinates[0]
    assert electrode.coordinates[1] == coordinates[1]
    assert electrode.coordinates[2] == coordinates[2]
    assert electrode.modality == "scan"
    assert electrode.label == None
    assert electrode.labeled == False
    assert electrode._cap_centroid == None
    assert electrode._mapped_to_unit_sphere == False
    assert electrode._registered == False
    assert electrode._undo_coordinates == None
