from view.surface_view import SurfaceView


def display_surface(surface_view: SurfaceView | None):
    if surface_view is not None:
        frame_size = surface_view.frame.size()
        surface_view.resize_view(frame_size.width(), frame_size.height())

        surface_view.show()
