import os
import datetime
from datetime import date
import sqlite3 as sl
from PIL import Image, ImageFilter, ImageEnhance, ImageFont, ImageDraw

from pylibdmtx.pylibdmtx import decode
from pylibdmtx.pylibdmtx import encode

from PySide6.QtSql import QSqlQueryModel
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QMainWindow, QDialog, QTableView, QHeaderView, QHBoxLayout, QSpinBox, QPushButton
from PySide6.QtWidgets import QLabel, QStatusBar, QComboBox, QWidget, QVBoxLayout, QFileDialog, QDateEdit
from PySide6.QtCore import Qt, QDateTime, QModelIndex
from PySide6 import QtPrintSupport, QtGui, QtCore, QtSql

from MainMenu import MainMenu
from ModelSKU import ModelSKU
from ToolBar import ToolBar
from progressBar import dlgProgressBar

import prerare


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
        self.setWindowTitle('Молочное море - PrintDM - GoDEX530')
        self.resize(800, 700)

        main_menu = MainMenu(self)
        main_menu.load_file.triggered.connect(self.load_file_triggered)
        main_menu.load_file_two.triggered.connect(self.load_file_two_triggered)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        tool_bar.load_file.triggered.connect(self.load_file_triggered)
        tool_bar.load_file_two.triggered.connect(self.load_file_two_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        layV = QVBoxLayout()
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

        layV.addWidget(lblSelectGroup)
        layV.addWidget(self.cbSelectGroup)
        layV.addWidget(self.tvSKU)
        layV.addLayout(layHDateDate)
        # layV.addLayout(layHCountCount)
        layV.addLayout(layHLabelSelectPrinter)
        layV.addWidget(btnPrint)
        # layV.addWidget(self.cbSelectPrinter)
        # layV.addWidget(self.tePrintInfo)
        # layV.addWidget(self.ppwMain)
        # layV.addWidget(btnPrint)
        layV.setAlignment(Qt.AlignmentFlag.AlignTop)

        container = QWidget()
        container.setLayout(layV)
        self.centralWidget()
        self.setCentralWidget(container)

    def load_file_two_triggered(self):
        print('load_file_two.triggered')
        dlg = dlgProgressBar()
        list = []
        dlg.exec()
        # list_cod = dlg.data
        # print(list_cod)
        print('fin')

    def btnPrint_clicked(self):
        print('btnPrint_clicked')
        # TODO Полный рефакторинг функции
        dt = datetime.datetime.strptime(self.deDate.text(), "%d.%m.%Y")
        current_date = datetime.datetime.today() - datetime.timedelta(days=1)
        if dt < current_date:
            QMessageBox.critical(self, 'Внимание', 'Измените дату')
        if int(self.sbCount.text()) == 0:
            QMessageBox.critical(self, 'Внимание', 'Введите количество')

        # TODO Проверка принтера !!!
        printer = QtPrintSupport.QPrinter(mode=QtPrintSupport.QPrinter.PrinterMode.PrinterResolution)

        painter = QtGui.QPainter()
        page_size = QtGui.QPageSize(QtCore.QSize(120, 57))
        printer.setPageSize(page_size)
        painter.begin(printer)

        n = self.tvSKU.currentIndex().row()
        p = self.tvSKU.model().index(n, 0).data()
        print(p)
        con = sl.connect('SFMDEX.db')
        cur = con.cursor()
        sql = f'SELECT id, prefix FROM sku WHERE gtin = "{p}"'
        cur.execute(sql)
        id_sku = cur.fetchone()
        print(id_sku[0], id_sku[1])
        sql = f'''SELECT count(prefix) FROM party WHERE prefix = "{id_sku[1]}" GROUP BY prefix'''
        cur.execute(sql)
        record = cur.fetchone()
        if not record:
            nameParty: str = id_sku[1] + '-' + '001'
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) VALUES ("{nameParty}", "{dateParty}", "{id_sku[1]}", 1)'''
        else:
            num: int = 1 + record[0]
            numberParty = str(num)
            prefixParty = id_sku[1]
            numberParty = numberParty.zfill(3)
            nameParty = prefixParty + '-' + numberParty
            print(numberParty, nameParty)
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) VALUES ("{nameParty}", "{dateParty}", "{prefixParty}", {num})'''
        cur.execute(sql)
        con.commit()


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
            # ввести соотвествующий учет
            dtext.text((130, 80), nameParty, font=font, fill=('#1C0606'))
            i += 1
            dtext.text((130, -10), str(i), font=font, fill=('#1C0606'))

            img.save('crop_img_cod.png')

            page_size = printer.pageRect(QtPrintSupport.QPrinter.Unit.DevicePixel)
            page_width = int(page_size.width())
            page_heigth = int(page_size.height())
            pixmap = QtGui.QPixmap('crop_img_cod.png')
            # pixmap = QtGui.QPixmap('enhancer_output.png')
            pixmap = pixmap.scaled(page_width, page_heigth, aspectMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio)
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
        row  = cur.fetchone()
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
            return
        filelist = filename.split('_')
        list_cod = prerare.convertPdfToJpg(filename)
        gtin: str = filelist[3]
        if not gtin.isnumeric():
            QMessageBox.critical(self, 'Внимание', 'gtin продукта не найден. Обратитесь к администратору')
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
