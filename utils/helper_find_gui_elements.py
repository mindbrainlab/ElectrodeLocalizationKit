from PyQt6.QtWidgets import QPushButton


def find_all_buttons(widget):
    buttons = []
    if isinstance(widget, QPushButton):
        buttons.append(widget)
    for child in widget.children():
        buttons.extend(find_all_buttons(child))
    return buttons


buttons = find_all_buttons(self)
for button in buttons:
    print(button.objectName())
