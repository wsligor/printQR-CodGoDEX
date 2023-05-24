from PySide6.QtWidgets import QMainWindow, QDialog
from PySide6.QtWidgets import QLabel, QStatusBar, QTextEdit, QComboBox, QPushButton, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6 import QtPrintSupport, QtGui, QtCore

from MainMenu import MainMenu
from ToolBar import ToolBar


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Класс QPrinterInfo')
        self.resize(800, 900)

        main_menu = MainMenu(self)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        layV = QVBoxLayout()
        lblSelectPrinter = QLabel('Выберите принтер:')
        self.cbSelectPrinter = QComboBox()
        self.cbSelectPrinter.addItems(QtPrintSupport.QPrinterInfo.availablePrinterNames())
        self.cbSelectPrinter.currentTextChanged[str].connect(self.showData)

        self.tePrintInfo = QTextEdit()
        self.tePrintInfo.setReadOnly(True)
        self.showData(self.cbSelectPrinter.currentText())

        self.printer = QtPrintSupport.QPrinter()
        # self.printer.setPageSize(QtCore.QSize(95, 57))
        self.ppwMain = QtPrintSupport.QPrintPreviewWidget(self.printer, parent=self)
        print(f'printer.PageRect = {self.printer.pageRect}')
        self.ppwMain.paintRequested.connect(self._PaintImage)

        btnPrint = QPushButton('Печать')
        btnPrint.clicked.connect(self.btnPrintClicked)

        layV.addWidget(lblSelectPrinter)
        layV.addWidget(self.cbSelectPrinter)
        layV.addWidget(self.tePrintInfo)
        layV.addWidget(self.ppwMain)
        layV.addWidget(btnPrint)

        container = QWidget()
        container.setLayout(layV)
        self.centralWidget()
        self.setCentralWidget(container)

    def btnPrintClicked(self):
        pd = QtPrintSupport.QPrintDialog(self.printer, parent=self)

        pd.setOptions(QtPrintSupport.QAbstractPrintDialog.PrintDialogOption.PrintToFile |
                      QtPrintSupport.QAbstractPrintDialog.PrintDialogOption.PrintSelection)
        if pd.exec() == QDialog.DialogCode.Accepted:
            self._PrintImage(self.printer)
        pass


    def _PaintImage(self, printer):
        painter = QtGui.QPainter()
        painter.begin(printer)
        pixmap = QtGui.QPixmap('img_encoded.jpg')
        pixmap = pixmap.scaled(printer.width(), printer.height(), aspectMode=Qt.AspectRatioMode.KeepAspectRatio)
        print(f'Paint width {printer.width()}, height {printer.height()}, PageRect {printer.pageRect}')
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        # self.ppwMain.exec()
        pass

    def _PrintImage(self, printer):
        painter = QtGui.QPainter()
        self.printer.setPageSize(QtCore.QSize(95, 57))
        painter.begin(printer)
        page_size = printer.pageRect(QtPrintSupport.QPrinter.Unit.DevicePixel)
        print(page_size.height(), page_size.width())
        pixmap = QtGui.QPixmap('img_encoded.jpg')
        # pixmap = pixmap.scaled(printer.width(), printer.height(), aspectMode=Qt.AspectRatioMode.KeepAspectRatio)
        pixmap = pixmap.scaled(page_size.height(), page_size.width(), aspectMode=Qt.AspectRatioMode.KeepAspectRatio)
        print(f'Print width {printer.width()}, height {printer.height()}')
        painter.drawPixmap(0, 0, pixmap)

        print(f'width {printer.width()}, height {printer.height()}')
        painter.end()


    def showData(self, name):
        printer = QtPrintSupport.QPrinterInfo.printerInfo(name)
        s = "Название: " + name + "\n\n"
        if printer.isDefault():
            s += "Принтер по умолчанию\n"
        s2 = printer.makeAndModel()
        if s != s2:
            s += "Полное название: " + s2 + "\n"
        s2 = printer.description()
        if s != s2:
            s += "Описание: " + s2 + "\n"
        if printer.isRemote():
            s += "Сетевой принтер\n"
        s2 = printer.location()
        if s2:
            s += "Расположение: " + s2 + "\n"
        s += "\n"
        match printer.state():
            case QtPrintSupport.QPrinter.PrinterState.Idle:
                s2 = "простаивает"
            case QtPrintSupport.QPrinter.PrinterState.Active:
                s2 = "идёт печать"
            case QtPrintSupport.QPrinter.PrinterState.Aborted:
                s2 = "печать прервана"
            case QtPrintSupport.QPrinter.PrinterState.Error:
                s2 = "возникла ошибка"
        s += "Состояние: " + s2 + "\n\n"
        s += "Размер бумаги по умолчанию: " + \
             printer.defaultPageSize().name() + "\n"
        s2 = ", ".join([s.name() for s in printer.supportedPageSizes()])
        if printer.supportsCustomPageSizes():
            s2 += ", произвольные размеры"
        s += "Поддерживаемые размеры бумаги: " + s2 + "\n"
        s += "Минимальный размер бумаги: " + \
             printer.minimumPhysicalPageSize().name() + "\n"
        s += "Максимальный размер бумаги: " + \
             printer.maximumPhysicalPageSize().name() + "\n\n"
        s += "Режим двусторонней печати по умолчанию: " + \
             self._getDuplexModeName(printer.defaultDuplexMode()) + "\n"
        s2 = ""
        for m in printer.supportedDuplexModes():
            if s2:
                s2 += ", "
            s2 += self._getDuplexModeName(m)
        s += "Поддерживаемые режимы двухсторонней печати: " + s2 + "\n\n"
        s += "Режим цветной печати по умолчанию: " + \
             self._getColorModeName(printer.defaultColorMode()) + "\n"
        s2 = ""
        for m in printer.supportedColorModes():
            if s2:
                s2 += ", "
            s2 += self._getColorModeName(m)
        s += "Поддерживаемые режимы цветной печати: " + s2 + "\n\n"
        s2 = ", ".join([str(r) for r in printer.supportedResolutions()])
        s += "Поддерживаемые разрешения, точек/дюйм: " + s2
        self.tePrintInfo.setText(s)

    @staticmethod
    def _getDuplexModeName(ident):
        match ident:
            case QtPrintSupport.QPrinter.DuplexMode.DuplexNone:
                return "односторонняя печать"
            case QtPrintSupport.QPrinter.DuplexMode.DuplexAuto:
                return "двухсторонняя печать с автоматическим выбором " + \
                    "стороны листа"
            case QtPrintSupport.QPrinter.DuplexMode.DuplexLongSide:
                return "двухсторонняя печать с переворотом листа вокруг " + \
                    "длинной стороны"
            case QtPrintSupport.QPrinter.DuplexMode.DuplexShortSide:
                return "двухсторонняя печать с переворотом листа вокруг " + \
                    "короткой стороны"

    @staticmethod
    def _getColorModeName(ident):
        match ident:
            case QtPrintSupport.QPrinter.ColorMode.Color:
                return "цветная печать"
            case QtPrintSupport.QPrinter.ColorMode.GrayScale:
                return "печать оттенками серого"
