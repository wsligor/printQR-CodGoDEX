import os

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMessageBox, QFileDialog

import prerare

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

        self.load_file = QAction(QIcon('icons\\qr-code.png'), 'Загрузить файл с кодами', self)
        # self.load_file.setShortcut('Alt+Q')
        self.load_file.setStatusTip('Загрузить файл с кодами')
        self.load_file.setToolTip('Загрузить файл с кодами')
        self.load_file.triggered.connect(self.load_file_triggered)

    def about_qt_triggered(self):
        QMessageBox.aboutQt(self)

    def about_triggered(self):
        title = 'О программе'
        text = 'О программе'
        QMessageBox.about(self, title, text)

    def load_file_triggered(self):
        print('load_file_triggered')
        filename = QFileDialog.getOpenFileName(self, 'Открыть файл', os.getcwd(), 'PDF files (*.pdf)')[0]
        print(filename)
        list_cod = prerare.convertPdfToJpg(filename)
        print(len(list_cod))

