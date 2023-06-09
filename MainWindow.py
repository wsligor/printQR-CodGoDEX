import os, shutil
import datetime
from datetime import date
import sqlite3 as sl
from PIL import Image, ImageFilter, ImageEnhance, ImageFont, ImageDraw
from PIL import Image as ImagePIL
import fitz

from pylibdmtx.pylibdmtx import decode
from pylibdmtx.pylibdmtx import encode

from PySide6.QtSql import QSqlQueryModel
from PySide6.QtWidgets import QMessageBox, QProgressBar
from PySide6.QtWidgets import QMainWindow, QDialog, QTableView, QHeaderView, QHBoxLayout, QSpinBox, QPushButton
from PySide6.QtWidgets import QLabel, QStatusBar, QComboBox, QWidget, QVBoxLayout, QFileDialog, QDateEdit
from PySide6.QtCore import Qt, QDateTime, QModelIndex, QThread
from PySide6 import QtPrintSupport, QtGui, QtCore, QtSql

from MainMenu import MainMenu
from ModelSKU import ModelSKU
from ToolBar import ToolBar

import prerare

# Масштаб преобразования pdf в jpg = 2.08
QR_IN_2_008 = (
    (38, 88, 170, 220), (248, 88, 380, 220), (458, 88, 590, 220), (668, 88, 798, 220), (880, 88, 1012, 220),
    (38, 446, 170, 578), (248, 446, 380, 578), (458, 446, 590, 578), (668, 446, 798, 578), (880, 446, 1012, 578),
    (38, 804, 170, 936), (248, 804, 380, 936), (458, 804, 590, 936), (668, 804, 798, 936), (880, 804, 1012, 936),
    (38, 1162, 170, 1294), (248, 1162, 380, 1294), (458, 1162, 590, 1294), (668, 1162, 798, 1294),
    (880, 1162, 1012, 1294)
)
# Масштаб преобразования pdf в jpg = 1
QR_IN_1 = (
    (19,  43, 81, 105), (120,  43, 182, 105), (221,  43, 283, 105), (322,  43, 384, 105), (423,  43, 485, 105),
    (19, 215, 81, 277), (120, 215, 182, 277), (221, 215, 283, 277), (322, 215, 384, 277), (423, 215, 485, 277),
    (19, 387, 81, 449), (120, 387, 182, 449), (221, 387, 283, 449), (322, 387, 384, 449), (423, 387, 485, 449),
    (19, 559, 81, 621), (120, 559, 182, 621), (221, 559, 283, 621), (322, 559, 384, 621), (423, 559, 485, 621)
)

# def retry(func):
#     def _wraper(*args, **kwargs):
#         func(*args, **kwargs)
#     return _wraper()

class threadCodJpgDecode(QThread):
    running = False
    signalStart = QtCore.Signal(int)
    signalExec = QtCore.Signal()
    signalFinished = QtCore.Signal(int, int)

    # method which will execute algorithm in another thread
    def __init__(self, fileName, id_sku, fn):
        super().__init__()
        self.fileName = fileName
        self.id_sku = id_sku
        self.fn = fn
        self.fileListCount = 0
        self.fileList = []

    def run(self):
        workingDirectory = os.getcwd() + '\\tmp\\'
        self.fileList = os.listdir(workingDirectory)
        for file in self.fileList:
            fullFileName = workingDirectory + file
            os.remove(fullFileName)
        self.convert_pdf2img(self.fileName)
        self.fileList = os.listdir(workingDirectory)
        self.signalStart.emit(len(self.fileList))
        defectCodeCount: int = 0
        list_cod = []
        for f in self.fileList:
            filename = workingDirectory + f
            img = ImagePIL.open(filename)
            for i in range(20):
                crop_img = img.crop(QR_IN_1[i])
                data = decode(crop_img)
                if data:
                    list_cod.append(data[0].data)
                else:
                    defectCodeCount += 1
                    crop_img.save(f'crop_img{i+defectCodeCount}.jpg')
            self.signalExec.emit()

        dateToday = date.today()
        list_cod_to_BD = []
        for cod in list_cod:
            str_list_cod = (self.id_sku, cod, 0, 0, dateToday)
            list_cod_to_BD.append(str_list_cod)

        con = sl.connect('SFMDEX.db')
        cur = con.cursor()
        sql = '''INSERT INTO codes(id_sku, cod, print, id_party, date_load) values(?,?,?,?,?)'''
        cur.executemany(sql, list_cod_to_BD)
        sql = f'''INSERT INTO file_load (name) values("{self.fn}")'''
        cur.execute(sql)
        con.commit()
        con.close()
        self.signalFinished.emit(len(list_cod_to_BD), defectCodeCount)

    def convert_pdf2img(self, filename: str):
        """Преобразует PDF в изображение и создает файл за страницей"""
        pdf_in = fitz.open(filename)
        i = 0
        for page in pdf_in:
            i += 1
            output_file = os.getcwd() + "\\tmp\\order" + str(i) + ".jpg"
            pix = page.get_pixmap()
            pix.save(output_file)
        pdf_in.close()

class ModelSelectGroup(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refreshSelectGroup()

    def refreshSelectGroup(self):
        sql = 'SELECT name, id FROM groups ORDER BY sort'
        self.setQuery(sql)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Молочное море - PrintDM - GoDEX530 - v1.0.1')
        self.resize(800, 700)
        self.dlg = None
        self.countProgress = 0
        self.codes = []

        main_menu = MainMenu(self)
        # main_menu.load_file.triggered.connect(self.load_file_triggered)
        main_menu.load_file.triggered.connect(self.load_file_two_triggered)
        main_menu.load_file.triggered.connect(self.load_file_triggered)
        main_menu.load_file_two.triggered.connect(self.load_file_two_triggered)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        # tool_bar.load_file.triggered.connect(self.load_file_triggered)
        tool_bar.load_file.triggered.connect(self.load_file_two_triggered)
        tool_bar.load_file.triggered.connect(self.load_file_triggered)
        tool_bar.load_file_two.triggered.connect(self.load_file_two_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        layV = QVBoxLayout()
        self.progressBar = QProgressBar()
        # self.progressBar.setMaximum(10)
        self.progressBar.setTextVisible(False)
        lblSelectGroup = QLabel('Выберите группу:')

        self.cbSelectGroup = QComboBox()
        self.modelSelectGrop = ModelSelectGroup()
        self.cbSelectGroup.setModel(self.modelSelectGrop)
        self.cbSelectGroup.currentTextChanged.connect(self.cbSelectGroup_currentTextChanged)

        self.tvSKU = QTableView()
        self.modelSKU = ModelSKU()
        self.tvSKU.setModel(self.modelSKU)
        self.tvSKU.setSelectionBehavior(self.tvSKU.SelectionBehavior.SelectRows)
        self.refreshSKU()

        lblDate = QLabel('Дата: ')
        self.deDate = QDateEdit()
        self.deDate.setMinimumWidth(300)
        self.deDate.setDate(date.today())

        lblCount = QLabel('Количество: ')
        self.sbCount = QSpinBox()
        self.sbCount.setValue(1)
        self.sbCount.setMinimumWidth(300)

        layHDateDate = QHBoxLayout()
        layHDateDate.addWidget(lblDate)
        layHDateDate.addWidget(self.deDate)
        layHDateDate.addWidget(lblCount)
        layHDateDate.addWidget(self.sbCount)
        layHDateDate.setAlignment(Qt.AlignmentFlag.AlignLeft)

        btnPrint = QPushButton('Печать')
        btnPrint.clicked.connect(self.btnPrint_clicked)

        lblSelectPrinter = QLabel('Выберите принтер: ')
        self.cbSelectPrinter = QComboBox()
        self.cbSelectPrinter.addItems(QtPrintSupport.QPrinterInfo.availablePrinterNames())
        self.cbSelectPrinter.currentTextChanged[str].connect(self.showData)
        layHLabelSelectPrinter = QHBoxLayout()
        layHLabelSelectPrinter.addWidget(lblSelectPrinter)
        layHLabelSelectPrinter.addWidget(self.cbSelectPrinter)
        layHLabelSelectPrinter.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layV.addWidget(self.progressBar)
        layV.addWidget(lblSelectGroup)
        layV.addWidget(self.cbSelectGroup)
        layV.addWidget(self.tvSKU)
        layV.addLayout(layHDateDate)
        layV.addLayout(layHLabelSelectPrinter)
        layV.addWidget(btnPrint)
        layV.setAlignment(Qt.AlignmentFlag.AlignTop)

        container = QWidget()
        container.setLayout(layV)
        self.centralWidget()
        self.setCentralWidget(container)

    def load_file_two_triggered(self):
        # print('load_file_two.triggered')
        filename: str = QFileDialog.getOpenFileName(self, 'Открыть файл', os.getcwd(), 'PDF files (*.pdf)')[0]
        if not filename: #проверка на пустую строку
            return
        fn = os.path.basename(filename)
        if self.checkingFileUpload(fn):
            QMessageBox.critical(self, 'Внимание', 'Этот файл уже загружен в БД')
            return
        filelist = filename.split('_')
        gtin: str = filelist[3]
        if not gtin.isnumeric():
            QMessageBox.critical(self, 'Внимание', 'Нарушен формат имени файла. Обратитесь к администратору')
            return

        con = sl.connect('SFMDEX.db')
        cur = con.cursor()
        sql = f'SELECT id FROM sku WHERE gtin = "{gtin}"'
        cur.execute(sql)
        row = cur.fetchone()
        if row is None:
            QMessageBox.critical(self, 'Внимание', 'gtin продукта не найден. Обратитесь к администратору')
            return
        id_sku = row[0]
        self.setCursor(Qt.CursorShape.WaitCursor)

        self.threadOne = threadCodJpgDecode(filename, id_sku, fn)
        self.threadOne.signalStart.connect(self.threadStartOne)
        self.threadOne.signalExec.connect(self.threadExecOne)
        self.threadOne.signalFinished.connect(self.threadFinishedTwo)
        self.threadOne.finished.connect(self.threadFinishedOne)
        self.threadOne.start()

    @QtCore.Slot()
    def threadStartOne(self, l):
        self.statusbar.showMessage('Загрузка кодов в БД ...')
        self.progressBar.setMaximum(l)


    @QtCore.Slot()
    def threadExecOne(self):
        self.countProgress += 1
        self.progressBar.setValue(self.countProgress)
        self.statusbar.showMessage('Загрузка кодов в БД ...')

    @QtCore.Slot()
    def threadFinishedOne(self):
        self.progressBar.setValue(0)
        self.countProgress = 0
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.modelSKU.modelRefreshSKU()

    @QtCore.Slot()
    def threadFinishedTwo(self, codeCount, defectCodeCount):
        self.statusbar.showMessage(f'Загружено {codeCount}, забраковано {defectCodeCount}', 2500)

    def btnPrint_clicked(self):
        # TODO Полный рефакторинг функции
        # TODO Проверить запрашиваемое количество кодов на печать
        printerName = self.cbSelectPrinter.currentText()
        if printerName != 'Godex G530':
            QMessageBox.critical(self, 'Attention', 'Установите принтер для печати этикеток')
            return
        dt = datetime.datetime.strptime(self.deDate.text(), "%d.%m.%Y")
        current_date = datetime.datetime.today() - datetime.timedelta(days=1)
        if dt < current_date:
            QMessageBox.critical(self, 'Внимание', 'Измените дату')
            return
        if int(self.sbCount.text()) == 0:
            QMessageBox.critical(self, 'Внимание', 'Введите количество')
            return

        n = self.tvSKU.currentIndex().row()
        p = self.tvSKU.model().index(n, 0).data()
        if n == -1:
            QMessageBox.information(self, 'Внимание', 'Выделите строку для печати')
            return

        con = sl.connect('SFMDEX.db')
        cur = con.cursor()

        sql = f'SELECT id, prefix FROM sku WHERE gtin = "{p}"'
        cur.execute(sql)
        id_sku = cur.fetchone()
        sql = f'SELECT count(cod) FROM codes WHERE id_sku = {id_sku[0]}'
        cur.execute(sql)
        record = cur.fetchone()
        if self.sbCount.value() > record[0]:
            QMessageBox.information(self, 'Внимание', 'Загрузите коды, не хватает для печати')
            return

        sql = f'''SELECT count(prefix) FROM party WHERE prefix = "{id_sku[1]}" GROUP BY prefix'''
        cur.execute(sql)
        record = cur.fetchone()
        num: int = 1
        if not record:
            nameParty: str = id_sku[1] + '-' + '001'
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) VALUES ("{nameParty}", "{dateParty}", "{id_sku[1]}", {num})'''
        else:
            num: int = 1 + record[0]
            numberParty = str(num)
            prefixParty = id_sku[1]
            numberParty = numberParty.zfill(3)
            nameParty = prefixParty + '-' + numberParty
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) VALUES ("{nameParty}", "{dateParty}", "{prefixParty}", {num})'''
        cur.execute(sql)
        con.commit()

        # TODO Проверка принтера !!!
        printer = QtPrintSupport.QPrinter(mode=QtPrintSupport.QPrinter.PrinterMode.PrinterResolution)
        painter = QtGui.QPainter()
        page_size = QtGui.QPageSize(QtCore.QSize(120, 57))
        printer.setPageSize(page_size)
        painter.begin(printer)

        sql = f"SELECT cod, id FROM codes WHERE id_sku = {id_sku[0]} AND print = 0 ORDER BY date_load LIMIT {int(self.sbCount.text())}"
        cur.execute(sql)
        codes_bd = cur.fetchall()

        i: int = 0

        for cod in codes_bd:
            encoded = encode(cod[0], scheme='', size='20x20')
            sql = f'''UPDATE codes SET print = 1, id_party = {num} WHERE id = "{cod[1]}"'''
            cur.execute(sql)
            con.commit()

            img_encod = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            # img_encoded = img_encod.resize((120, 120))
            img_filter = img_encod.filter(ImageFilter.EDGE_ENHANCE)
            img_filter.save('img_filter.png')

            enhancer = ImageEnhance.Contrast(img_filter)
            factor = 50
            enhancer_output = enhancer.enhance(factor)
            enhancer_output.save('enhancer_output.png')

            img_encod.save('img_encoded.png')

            img = Image.new('RGB', (454, 238), 'white')
            img_cod = Image.open('enhancer_output.png')
            img.paste(img_cod, (5, 5))
            font = ImageFont.truetype('ARIALNBI.TTF', size=40)
            dtext = ImageDraw.Draw(img)
            dtext.text((130, 25), self.deDate.text(), font=font, fill=('#1C0606'))
            # TODO получить номера партионного учета
            # ввести соответствующий учет
            dtext.text((130, 80), nameParty, font=font, fill=('#1C0606'))
            i += 1
            dtext.text((130, -10), str(i), font=font, fill=('#1C0606'))

            img.save('crop_img_cod.png')

            page_size = printer.pageRect(QtPrintSupport.QPrinter.Unit.DevicePixel)
            page_width = int(page_size.width())
            page_height = int(page_size.height())
            pixmap = QtGui.QPixmap('crop_img_cod.png')
            # pixmap = QtGui.QPixmap('enhancer_output.png')
            pixmap = pixmap.scaled(page_width, page_height, aspectMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            painter.drawPixmap(20, 50, pixmap)
            printer.newPage()

        painter.end()
        con.close()
        self.modelSKU.modelRefreshSKU()

    def checkingFileUpload(self, filename):
        sql = f'''SELECT COUNT(name) FROM file_load WHERE name = "{filename}"'''
        con = sl.connect('SFMDEX.db')
        cur = con.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        if row[0] == 0:
            return False
        else:
            return True

    def load_file_triggered(self):
        # TODO проверить gtin в базе если нет выдать предупреждение
        con = sl.connect('SFMDEX.db')
        cur = con.cursor()
        filename: str = QFileDialog.getOpenFileName(self, 'Открыть файл', os.getcwd(), 'PDF files (*.pdf)')[0]
        fn = os.path.basename(filename)
        if self.checkingFileUpload(fn):
            QMessageBox.critical(self, 'Внимание', 'Этот файл уже загружен в БД')
            # return
        filelist = filename.split('_')
        list_cod = prerare.convertPdfToJpg(filename)
        gtin: str = filelist[3]
        if not gtin.isnumeric():
            QMessageBox.critical(self, 'Внимание', 'gtin продукта не найден. Обратитесь к администратору')
            return
        sql = f'SELECT id FROM sku WHERE gtin = "{gtin}"'
        cur.execute(sql)
        row = cur.fetchone()
        id_sku = row[0]
        dateToday = date.today()
        list_cod_to_BD = []
        for cod in list_cod:
            str_list_cod = (id_sku, cod, 0, 0, dateToday)
            list_cod_to_BD.append(str_list_cod)
        sql = '''INSERT INTO codes(id_sku, cod, print, id_party, date_load) values(?,?,?,?,?)'''
        cur.executemany(sql, list_cod_to_BD)
        sql = f'''INSERT INTO file_load (name) values("{fn}")'''
        cur.execute(sql)
        con.commit()
        con.close()
        self.modelSKU.modelRefreshSKU()
        QMessageBox.information(self, 'Все', 'Все')


    def refreshSKU(self):
        hh = self.tvSKU.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv = self.tvSKU.verticalHeader()
        hv.hide()


    def cbSelectGroup_currentTextChanged(self, name):
        print(name)
        sql = f'SELECT id FROM groups WHERE name = "{name}"'
        print(sql)
        query = QtSql.QSqlQuery()
        query.exec(sql)
        if query.isActive():
            query.first()
            i = query.value('id')
            print(i)
        self.modelSKU.modelRefreshSKU(i)
        # self.refreshSKU()

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
        self.cbSelectPrinter.setCurrentText(s)
        # self.tePrintInfo.setText(s)

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
