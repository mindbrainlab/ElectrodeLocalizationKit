import vedo as vd
import numpy as np
import vtk
    
def compute_distance_between_coordinates(coordinates_1: np.ndarray, coordinates_2: np.ndarray) -> float:
    """Returns the distance between two electrodes."""
    return np.linalg.norm(coordinates_1-coordinates_2)
    
def normalize_mesh(mesh: vd.Mesh) -> float:
    """Scale Mesh average size to unit."""
    coords = mesh.points()
    coords = np.array(mesh.points())
    if not coords.shape[0]:
        return 1.0
    cm = np.mean(coords, axis=0)
    pts = coords - cm
    xyz2 = np.sum(pts * pts, axis=0)
    scale = 1 / np.sqrt(np.sum(xyz2) / len(pts))
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(scale, scale, scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    mesh._update(tf.GetOutput())
    return scale

def rescale_to_original_size(mesh: vd.Mesh, scale: float) -> float:
    """Rescale Mesh to original size."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(1/scale, 1/scale, 1/scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    mesh._update(tf.GetOutput())
    return 1.0