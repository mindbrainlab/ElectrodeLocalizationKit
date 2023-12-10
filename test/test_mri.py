import vedo as vd

import nibabel as nib

filename = 'sample_data/bem_outer_skin_surface.gii'

img = nib.load(filename) # type: ignore

verts = img.darrays[0].data # type: ignore
cells = img.darrays[1].data # type: ignore

# Build the polygonal Mesh object from the vertices and faces
mesh = vd.Mesh([verts, cells])

# Set the backcolor of the mesh to violet
# and show edges with a linewidth of 2
mesh.color('violet')

print(dir(mesh))

# Show the mesh, vertex labels, and docstring
vd.show(mesh, [], __doc__, viewup='z', axes=1).close()