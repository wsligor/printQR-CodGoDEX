from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMessageBox


class BaseAction(QAction):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.about_qt = QAction(QIcon('icons\\qt.png'), 'О библиотеке Qt', self)
        self.about_qt.setShortcut('Ctrl+Q')
        self.about_qt.setStatusTip('Показать "О библиотеке Qt"')
        self.about_qt.setToolTip('Показать "О библиотеке Qt"')
        self.about_qt.triggered.connect(self.about_qt_triggered)

        self.about = QAction(QIcon('icons\\info.png'), 'О программе', self)
        # self.about.setShortcut('Ctrl+Q')
        self.about.setStatusTip('Показать "О программе"')
        self.about.setToolTip('Показать "О программе"')
        self.about.triggered.connect(self.about_triggered)

    def about_qt_triggered(self):
        QMessageBox.aboutQt(self)

    def about_triggered(self):
        title = 'О программе'
        text = 'О программе'
        QMessageBox.about(self, title, text)