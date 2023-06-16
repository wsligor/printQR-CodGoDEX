import os
import datetime
import fitz
import configparser
import sqlite3 as sl

from datetime import date
from PIL import Image, ImageFont, ImageDraw
from PIL.ImageQt import ImageQt
from PIL import Image as ImagePIL
from pylibdmtx.pylibdmtx import decode
from pylibdmtx.pylibdmtx import encode

from PySide6.QtGui import QAction, QGuiApplication, QImage
from PySide6.QtSql import QSqlQueryModel
from PySide6.QtWidgets import QMessageBox, QProgressBar
from PySide6.QtWidgets import QMainWindow, QTableView, QHeaderView, QHBoxLayout, QSpinBox, QPushButton
from PySide6.QtWidgets import QLabel, QStatusBar, QComboBox, QWidget, QVBoxLayout, QFileDialog, QDateEdit
from PySide6.QtCore import Qt, QThread
from PySide6 import QtPrintSupport, QtGui, QtCore, QtSql

from MainMenu import MainMenu
from ModelSKU import ModelSKU
from ToolBar import ToolBar
from SetupWindow import SetupWindow


# TODO Добавить дату выбытия кода

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

        dateToday = date.today().strftime('%d.%m.%Y')
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

class ModelSelectCompany(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refresdSelectCompany()

    def refresdSelectCompany(self):
        sql = 'SELECT name, id FROM company ORDER BY id'
        self.setQuery(sql)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Молочное море/Биорич - PrintDM - GoDEX530 - v1.0.3')
        self.resize(800, 700)
        self.dlg = None
        self.countProgress = 0
        self.codes = []
        self.id_company = None
        self.id_groups = None
        self.LabelType = ''
        self.PrinterControl = ''

        main_menu = MainMenu(self)
        # main_menu.load_file.triggered.connect(self.load_file_triggered)
        main_menu.load_file_two.triggered.connect(self.load_file_two_triggered)
        main_menu.setup.triggered.connect(self.setupDialog_triggered)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        # tool_bar.load_file.triggered.connect(self.load_file_triggered)
        tool_bar.load_file_two.triggered.connect(self.load_file_two_triggered)
        tool_bar.setup.triggered.connect(self.setupDialog_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        layV = QVBoxLayout()
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(False)

        lblSelectGroup = QLabel('Выберите группу:')
        self.cbSelectGroup = QComboBox()
        self.modelSelectGrop = ModelSelectGroup()
        self.cbSelectGroup.setModel(self.modelSelectGrop)
        self.cbSelectGroup.currentTextChanged.connect(self.cbSelectGroup_currentTextChanged)
        layVselectGroup = QVBoxLayout()
        layVselectGroup.addWidget(lblSelectGroup)
        layVselectGroup.addWidget(self.cbSelectGroup)

        lblSelectCompany = QLabel('Выберите предприятие')
        self.cbSelectCompany = QComboBox()
        self.modelSelectCompany = ModelSelectCompany()
        self.cbSelectCompany.setModel(self.modelSelectCompany)
        self.cbSelectCompany.currentTextChanged.connect(self.cbSelectCompany_currentTextChanged)
        layVselectCompany = QVBoxLayout()
        layVselectCompany.addWidget(lblSelectCompany)
        layVselectCompany.addWidget(self.cbSelectCompany)

        layHGroupCompany = QHBoxLayout()
        layHGroupCompany.addLayout(layVselectGroup)
        layHGroupCompany.addLayout(layVselectCompany)

        self.tvSKU = QTableView()
        self.modelSKU = ModelSKU()
        self.tvSKU.setModel(self.modelSKU)
        self.tvSKU.setSelectionBehavior(self.tvSKU.SelectionBehavior.SelectRows)
        self.refreshSKU()

        lblDate = QLabel('Дата: ')
        self.deDate = QDateEdit()
        self.deDate.setMinimumWidth(300)
        self.deDate.setDate(date.today())
        self.deDate.setDisplayFormat('dd.MM.yyyy')

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
        layHLabelSelectPrinter = QHBoxLayout()
        layHLabelSelectPrinter.addWidget(lblSelectPrinter)
        layHLabelSelectPrinter.addWidget(self.cbSelectPrinter)
        layHLabelSelectPrinter.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layV.addWidget(self.progressBar)
        layV.addLayout(layHGroupCompany)
        layV.addWidget(self.tvSKU)
        layV.addLayout(layHDateDate)
        layV.addLayout(layHLabelSelectPrinter)
        layV.addWidget(btnPrint)
        layV.setAlignment(Qt.AlignmentFlag.AlignTop)

        container = QWidget()
        container.setLayout(layV)
        self.centralWidget()
        self.setCentralWidget(container)

        self.readConfigINI()
        self._createContextMenuTableSKU()

    def _createContextMenuTableSKU(self):
        print('_createContextMenuTableSKU')
        self.tvSKU.setContextMenuPolicy(Qt.ActionsContextMenu)
        copyGtinAction = QAction('копировать GTIN', self)
        copyGtinAction.triggered.connect(self.copyGtinAction)
        self.tvSKU.addAction(copyGtinAction)


    def copyGtinAction(self):
        print('copyGtinAction')
        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(selectGTIN)



    def readConfigINI(self):
        config = configparser.ConfigParser()
        config.read('setting.ini')
        default = config['DEFAULT']
        self.LabelType = default['LabelType']
        self.PrinterControl = default['PrinterControl']

    def setupDialog_triggered(self):
        dlg = SetupWindow()
        dlg.exec()
        self.readConfigINI()

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
    def threadStartOne(self, maxValueProgressBar):
        self.statusbar.showMessage('Загрузка кодов в БД ...')
        self.progressBar.setMaximum(maxValueProgressBar)

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
        self.modelSKU.modelRefreshSKU(self.id_company, id_groups=None)

    @QtCore.Slot()
    def threadFinishedTwo(self, codeCount, defectCodeCount):
        self.statusbar.showMessage(f'Загружено {codeCount}, забраковано {defectCodeCount}', 2500)

    def btnPrint_clicked(self):
        printerName = self.cbSelectPrinter.currentText()
        if printerName != self.PrinterControl:
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
        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()
        if selectIndexTableSKU == -1:
            QMessageBox.information(self, 'Внимание', 'Выделите строку для печати')
            return

        con = sl.connect('SFMDEX.db')
        cur = con.cursor()

        sql = f'SELECT id, prefix FROM sku WHERE gtin = "{selectGTIN}"'
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
        numParty: int = 1
        if not record:
            nameParty: str = id_sku[1] + '-' + '001'
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) 
                        VALUES ("{nameParty}", "{dateParty}", "{id_sku[1]}", {numParty})'''
        else:
            numParty: int = 1 + record[0]
            numberParty = str(numParty)
            prefixParty = id_sku[1]
            numberParty = numberParty.zfill(3)
            nameParty = prefixParty + '-' + numberParty
            dateParty = self.deDate.text()
            sql = f'''INSERT INTO party (name, date_doc, prefix, number) 
                        VALUES ("{nameParty}", "{dateParty}", "{prefixParty}", {numParty})'''
        cur.execute(sql)
        id_party = cur.lastrowid
        con.commit()

        printer = QtPrintSupport.QPrinter(mode=QtPrintSupport.QPrinter.PrinterMode.PrinterResolution)
        painter = QtGui.QPainter()
        page_size = QtGui.QPageSize(QtCore.QSize(92, 57))
        printer.setPageSize(page_size)

        sql = f'''SELECT cod, id FROM codes 
                    WHERE id_sku = {id_sku[0]} AND print = 0 ORDER BY date_load ASC LIMIT {self.sbCount.value()}'''
        cur.execute(sql)
        codes_bd = cur.fetchall()

        for index, cod in enumerate(codes_bd):
            painter.begin(printer)
            encoded = encode(cod[0], scheme='', size='20x20')
            img_encod = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)

            sql = f'''UPDATE codes SET print = 1, id_party = {id_party}, date_output = "{self.deDate.text()}" WHERE id = "{cod[1]}"'''
            cur.execute(sql)
            con.commit()

            img = Image.new('RGB', (354, 236), 'white')
            img.paste(img_encod, (0, 0))
            font = ImageFont.truetype('ARIALNBI.TTF', size=32)
            dtext = ImageDraw.Draw(img)

            if self.LabelType == 'DMCodDatePartyNumber':
                dtext.text((130, 40), self.deDate.text(), font=font, fill=('#1C0606'))
                dtext.text((130, 80), nameParty, font=font, fill=('#1C0606'))
                dtext.text((130, 0), str(index+1), font=font, fill=('#1C0606'))
            elif self.LabelType == 'OnlyDMCod':
                dtext.text((130, 0), str(index+1), font=font, fill=('#1C0606'))

            pixmap = QtGui.QPixmap(ImageQt(img))
            painter.drawPixmap(100, 50, pixmap)
            painter.end()
        painter.begin(printer)
        painter.end()
        con.close()
        self.modelSKU.modelRefreshSKU(self.id_company, self.id_groups)

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

    def refreshSKU(self):
        hh = self.tvSKU.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv = self.tvSKU.verticalHeader()
        hv.hide()

    def cbSelectGroup_currentTextChanged(self, name): # Выбор группы
        sql = f'SELECT id FROM groups WHERE name = "{name}"'
        query = QtSql.QSqlQuery()
        query.exec(sql)
        if query.isActive():
            query.first()
            id_groups = query.value('id')
            self.id_groups = id_groups
        self.modelSKU.modelRefreshSKU(self.id_company, id_groups)

    def cbSelectCompany_currentTextChanged(self, name): # Выбор кампании
        sql = f'SELECT id FROM company WHERE name = "{name}"'
        query = QtSql.QSqlQuery()
        query.exec(sql)
        if query.isActive():
            query.first()
            id_company = query.value('id')
            self.id_company = id_company
        self.cbSelectGroup.setCurrentIndex(0)
        self.modelSKU.modelRefreshSKU(id_company, id_groups=None)
