from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QToolBar
from PySide6 import QtGui

from BaseAction import BaseAction

class ToolBar(QToolBar, BaseAction):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMovable(False)

        # self.addAction(self.load_file)
        self.addAction(self.load_file_two)
        self.addAction(self.setup)
        self.addAction(self.about_qt)
        self.addAction(self.about)


