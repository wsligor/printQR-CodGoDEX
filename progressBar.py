import os
import time

from PIL import Image as ImagePIL
from PySide6.QtGui import QColor
from pylibdmtx.pylibdmtx import decode

from PySide6 import QtCore
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtWidgets import QProgressBar, QTextEdit
from PySide6.QtWidgets import QDialog, QTextEdit, QLineEdit, QComboBox, QDateEdit, QHeaderView, QFileDialog
from PySide6.QtWidgets import QTableView, QMessageBox, QHBoxLayout, QVBoxLayout, QPushButton, QToolButton, QLabel
from PySide6.QtSql import QSqlQueryModel

QR_IN = (
    (38, 88, 170, 220), (248, 88, 380, 220), (458, 88, 590, 220), (668, 88, 798, 220), (880, 88, 1012, 220),
    (38, 446, 170, 578), (248, 446, 380, 578), (458, 446, 590, 578), (668, 446, 798, 578), (880, 446, 1012, 578),
    (38, 804, 170, 936), (248, 804, 380, 936), (458, 804, 590, 936), (668, 804, 798, 936), (880, 804, 1012, 936),
    (38, 1162, 170, 1294), (248, 1162, 380, 1294), (458, 1162, 590, 1294), (668, 1162, 798, 1294),
    (880, 1162, 1012, 1294)
)

class BrowserHandlerOne(QtCore.QObject):
    running = False
    newTextAndColorOne = QtCore.Signal()
    finishedSignalOne = QtCore.Signal(list)

    # method which will execute algorithm in another thread
    def __init__(self, fileList):
        super().__init__()
        self.fileList = fileList

    def run(self):
        print(self.fileList)
        list_cod = []
        for f in self.fileList:
            filename = os.getcwd() + '\\tmp\\' + f
            img = ImagePIL.open(filename)
            for i in range(20):
                crop_img = img.crop(QR_IN[i])
                data = decode(crop_img)
                list_cod.append(data[0].data)
            self.newTextAndColorOne.emit()
        print(f't1 = {list_cod}')
        self.finishedSignalOne.emit(list_cod)

class BrowserHandlerTwo(QtCore.QObject):
    running = False
    newTextAndColorTwo = QtCore.Signal()
    finishedSignalTwo = QtCore.Signal(list)

    def __init__(self, fileList):
        super().__init__()
        self.fileList = fileList

    # method which will execute algorithm in another thread
    def run(self):
        print(self.fileList)
        list_cod = []
        for f in self.fileList:
            filename = os.getcwd() + '\\tmp\\' + f
            img = ImagePIL.open(filename)
            for i in range(20):
                crop_img = img.crop(QR_IN[i])
                data = decode(crop_img)
                list_cod.append(data[0].data)
            self.newTextAndColorTwo.emit()
        print(f't2 = {list_cod}')
        self.finishedSignalTwo.emit(list_cod)


class dlgProgressBar(QDialog):
    def __init__(self, data=[], parent=None):
        super().__init__(parent)
        self.data = data
        self.countProgress = 0

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(8)
        self.lblInfo = QLabel('Идет подготовка файлов...')
        layV = QVBoxLayout(self)
        layV.addWidget(self.progressBar)
        layV.addWidget(self.lblInfo)
        self.setLayout(layV)

        files = os.listdir(os.getcwd() + '\\tmp\\')
        print(files)
        half = len(files)//2
        partOne = files[:half]
        print(partOne)
        partTwo = files[half:]
        print(partTwo)
        # create thread
        self.threadOne = QtCore.QThread()
        # create object which will be moved to another thread
        self.browserHandlerOne = BrowserHandlerOne(partOne)
        # move object to another thread
        self.browserHandlerOne.moveToThread(self.threadOne)
        # after that, we can connect signals from this object to slot in GUI thread
        self.browserHandlerOne.newTextAndColorOne.connect(self.addNewTextAndColorOne)
        # connect started signal to run method of object in another thread
        self.threadOne.started.connect(self.browserHandlerOne.run)

        self.threadTwo = QtCore.QThread()
        self.browserHandlerTwo = BrowserHandlerTwo(partTwo)
        self.browserHandlerTwo.moveToThread(self.threadTwo)
        self.browserHandlerTwo.newTextAndColorTwo.connect(self.addNewTextAndColorTwo)
        self.browserHandlerTwo.finishedSignalTwo.connect(self.threadFinishedOne)
        self.threadTwo.started.connect(self.browserHandlerTwo.run)
        # start thread
        self.threadOne.start()
        self.threadTwo.start()



    @QtCore.Slot()
    def addNewTextAndColorOne(self):
            self.countProgress += 1
            self.progressBar.setValue(self.countProgress)

    @QtCore.Slot()
    def addNewTextAndColorTwo(self):
            self.countProgress += 1
            self.progressBar.setValue(self.countProgress)

    @QtCore.Slot()
    def threadFinishedOne(self, cod):
        self.data = self.data + cod
        print(self.data)
        self.accept()