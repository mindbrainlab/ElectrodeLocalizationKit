def connect_proceed_buttons(self):
    self.ui.proceed_button_0.clicked.connect(lambda: self.model.make_data_snapshot())
    self.ui.proceed_button_1.clicked.connect(lambda: self.model.make_data_snapshot())
    self.ui.proceed_button_2.clicked.connect(lambda: self.model.make_data_snapshot())
    self.ui.proceed_button_3.clicked.connect(lambda: self.model.make_data_snapshot())
    self.ui.proceed_button_4.clicked.connect(lambda: self.model.make_data_snapshot())


def connect_back_buttons(self):
    self.ui.restart_button_2.clicked.connect(lambda: self.model.restore_data_snapshot())

    self.ui.restart_button_3.clicked.connect(lambda: self.model.restore_data_snapshot())
    self.ui.restart_button_3.clicked.connect(
        lambda: self.headmodels["scan"].undo_registration(self.surface_registrator)
    )

    self.ui.restart_button_4.clicked.connect(lambda: self.model.restore_data_snapshot())
