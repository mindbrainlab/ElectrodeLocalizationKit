from ui.callbacks.refresh import (
    refresh_views_on_tab_change,
    refresh_views_on_resize,
)


def connect_tab_changed(self):
    self.ui.tabWidget.currentChanged.connect(
        lambda: refresh_views_on_tab_change(self.ui.tabWidget, self.views)
    )


def connect_splitter_moved(self):
    self.ui.splitter.splitterMoved.connect(
        lambda: refresh_views_on_resize(
            self.views,
            self.images,
            [
                ("scan", self.ui.headmodel_frame),
                ("mri", self.ui.mri_frame),
                ("labeling_main", self.ui.labeling_main_frame),
                ("labeling_reference", self.ui.labeling_reference_frame),
            ],
            self.ui.texture_frame,
        )
    )
