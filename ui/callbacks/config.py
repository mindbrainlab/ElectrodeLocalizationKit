from view.surface_view import SurfaceView


def update_view_config(
    view: SurfaceView | None,
    sphere_size: float,
    draw_flagposts: bool,
    flagpost_height: float,
    flagpost_size: float,
):

    if view is not None:
        config = {
            "sphere_size": sphere_size,
            "draw_flagposts": draw_flagposts,
            "flagpost_height": flagpost_height,
            "flagpost_size": flagpost_size,
        }
        view.update_config(config)
