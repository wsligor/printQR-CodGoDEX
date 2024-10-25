from PySide6.QtWidgets import QToolBar

from BaseAction import BaseAction

class ToolBar(QToolBar, BaseAction):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMovable(False)

        self.addAction(self.load_file_eps)
        self.addAction(self.about_qt)
        self.addAction(self.about)


