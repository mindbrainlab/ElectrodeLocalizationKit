import vedo as vd
from vedo import utils
import numpy as np

# import vtk
import vedo.vtkclasses as vtk


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
    t.Scale(1 / scale, 1 / scale, 1 / scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    mesh._update(tf.GetOutput())
    return 1.0


def align_with_landmarks(
    mesh, source_landmarks, target_landmarks, rigid=False, affine=False, least_squares=False
):
    """
    Transform mesh orientation and position based on a set of landmarks points.
    The algorithm finds the best matching of source points to target points
    in the mean least square sense, in one single step.

    If `affine` is True the x, y and z axes can scale independently but stay collinear.
    With least_squares they can vary orientation.

    Examples:
        - [align5.py](https://github.com/marcomusy/vedo/tree/master/examples/basic/align5.py)

            ![](https://vedo.embl.es/images/basic/align5.png)
    """

    if utils.is_sequence(source_landmarks):
        ss = vtk.vtkPoints()
        for p in source_landmarks:
            ss.InsertNextPoint(p)
    else:
        ss = source_landmarks.dataset.GetPoints()
        if least_squares:
            source_landmarks = source_landmarks.vertices

    if utils.is_sequence(target_landmarks):
        st = vtk.vtkPoints()
        for p in target_landmarks:
            st.InsertNextPoint(p)
    else:
        st = target_landmarks.GetPoints()
        if least_squares:
            target_landmarks = target_landmarks.vertices

    if ss.GetNumberOfPoints() != st.GetNumberOfPoints():
        n1 = ss.GetNumberOfPoints()
        n2 = st.GetNumberOfPoints()
        vd.logger.error(f"source and target have different nr of points {n1} vs {n2}")
        raise RuntimeError()

    if int(rigid) + int(affine) + int(least_squares) > 1:
        vd.logger.error("only one of rigid, affine, least_squares can be True at a time")
        raise RuntimeError()

    lmt = vtk.vtkLandmarkTransform()
    lmt.SetSourceLandmarks(ss)
    lmt.SetTargetLandmarks(st)
    lmt.SetModeToSimilarity()

    if rigid:
        lmt.SetModeToRigidBody()
        lmt.Update()

    elif affine:
        lmt.SetModeToAffine()
        lmt.Update()

    elif least_squares:
        cms = source_landmarks.mean(axis=0)
        cmt = target_landmarks.mean(axis=0)
        m = np.linalg.lstsq(source_landmarks - cms, target_landmarks - cmt, rcond=None)[0]
        M = vtk.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                M.SetElement(j, i, m[i][j])
        lmt = vtk.vtkTransform()
        lmt.Translate(cmt)
        lmt.Concatenate(M)
        lmt.Translate(-cms)

    else:
        lmt.Update()

    mesh.apply_transform(lmt)
    mesh.pipeline = utils.OperationNode("transform_with_landmarks", parents=[mesh])
    return lmt


def arrayFromVTKMatrix(vmatrix):
    """Return vtkMatrix4x4 or vtkMatrix3x3 elements as numpy array.
    The returned array is just a copy and so any modification in the array will not affect the input matrix.
    To set VTK matrix from a numpy array, use :py:meth:`vtkMatrixFromArray` or
    :py:meth:`updateVTKMatrixFromArray`.

    Function retrieved from
    https://github.com/Slicer/Slicer/blob/e53e8af9c4a0b60adee28b5eca5fc1b5ff2da9ea/Base/Python/slicer/util.py#L1114-L1151
    """
    from vtk import vtkMatrix4x4
    from vtk import vtkMatrix3x3
    import numpy as np

    if isinstance(vmatrix, vtkMatrix4x4):
        matrixSize = 4
    elif isinstance(vmatrix, vtkMatrix3x3):
        matrixSize = 3
    else:
        raise RuntimeError("Input must be vtk.vtkMatrix3x3 or vtk.vtkMatrix4x4")
    narray = np.eye(matrixSize)

    vmatrix.DeepCopy(narray.ravel(), vmatrix)  # type: ignore

    return narray
