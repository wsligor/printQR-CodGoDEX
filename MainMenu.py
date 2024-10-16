from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenuBar, QMessageBox, QMenu, QToolBar, QWidget

from BaseAction import BaseAction


class MainMenu(QMenuBar, BaseAction):
    def __init__(self, parent=None):
        super().__init__(parent)

        service_menu = QMenu("Service", self)
        # service_menu.addAction(self.load_file)
        service_menu.addAction(self.load_file_two)
        service_menu.addAction(self.load_file_eps)
        service_menu.addAction(self.setup)
        self.addMenu(service_menu)

        help_menu = QMenu("&Help", self)
        help_menu.addAction(self.about_qt)
        help_menu.addAction(self.about)
        self.addMenu(help_menu)
