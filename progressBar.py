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
    finishedSignal = QtCore.Signal()

    # method which will execute algorithm in another thread
    def __init__(self, count_page):
        super().__init__()
        self.count_page = count_page

    def run(self):
        print(self.count_page)
        # count_page = 11
        list_cod = []
        # for y in range(1, self.count_page+1, 2):
        for y in range(1, 10-1):
            filename = os.getcwd() + '\\tmp\\order' + str(y) + '.jpg'
            print(filename)
            # img = ImagePIL.open(filename)
            for i in range(20):
                # crop_img = img.crop(QR_IN[i])
                # data = decode(crop_img)
                # list_cod.append(data[0].data)
                print(i)
            self.newTextAndColorOne.emit()
        print('t1')
        self.finishedSignal.emit()


class BrowserHandlerTwo(QtCore.QObject):
    running = False
    newTextAndColorTwo = QtCore.Signal()
    finishedSignal = QtCore.Signal()

    def __init__(self, count_page):
        super().__init__()
        self.count_page = count_page

    # method which will execute algorithm in another thread
    def run(self):
        print(self.count_page)
        # count_page = 11
        list_cod = []
        # for y in range(2, self.count_page+1, 2):
        for y in range(10):
            # filename = os.getcwd() + '\\tmp\\order' + str(y) + '.jpg'
            # img = ImagePIL.open(filename)
            print('y')
            for i in range(20):
                # crop_img = img.crop(QR_IN[i])
                # data = decode(crop_img)
                # list_cod.append(data[0].data)
                print(x)
            self.newTextAndColorTwo.emit()
        print('t2')
        self.finishedSignal.emit()


class dlgProgressBar(QDialog):
    def __init__(self, data=[], parent=None):
        super().__init__(parent)
        self.data = data
        self.countProgress = 0

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(10)
        self.lblInfo = QLabel('Идет подготовка файлов...')
        layV = QVBoxLayout(self)
        layV.addWidget(self.progressBar)
        layV.addWidget(self.lblInfo)

        # create thread
        self.threadOne = QtCore.QThread()
        # create object which will be moved to another thread
        self.browserHandlerOne = BrowserHandlerOne(11)
        # move object to another thread
        self.browserHandlerOne.moveToThread(self.threadOne)
        # after that, we can connect signals from this object to slot in GUI thread
        self.browserHandlerOne.newTextAndColorOne.connect(self.addNewTextAndColorOne)
        # connect started signal to run method of object in another thread
        self.threadOne.started.connect(self.browserHandlerOne.run)

        self.threadTwo = QtCore.QThread()
        self.browserHandlerTwo = BrowserHandlerTwo(11)
        self.browserHandlerTwo.moveToThread(self.threadTwo)
        self.browserHandlerTwo.newTextAndColorTwo.connect(self.addNewTextAndColorTwo)
        self.browserHandlerTwo.finishedSignal.connect(self.threadFinished)
        self.threadTwo.started.connect(self.browserHandlerTwo.run)
        # start thread
        self.threadOne.start()
        # self.threadTwo.start()



    @QtCore.Slot(int, object)
    def addNewTextAndColorOne(self):
            self.countProgress += 1
            self.progressBar.setValue(self.countProgress)

    @QtCore.Slot(int, object)
    def addNewTextAndColorTwo(self):
            self.countProgress += 1
            self.progressBar.setValue(self.countProgress)

    def threadFinished(self):
        print('1')
        # self.accept()