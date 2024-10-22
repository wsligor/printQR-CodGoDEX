# import configparser
import logging
import os
import socket
import sqlite3 as sl
from datetime import date
from datetime import datetime
from typing import List, Tuple, Any

import win32print
from PySide6 import QtCore, QtSql
from PySide6.QtCore import Qt, QThread, QModelIndex, Signal
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtSql import QSqlQueryModel
from PySide6.QtWidgets import QLabel, QStatusBar, QComboBox, QWidget, QVBoxLayout, QFileDialog, QDateEdit, QDialog
from PySide6.QtWidgets import QMainWindow, QTableView, QHeaderView, QHBoxLayout, QSpinBox, QPushButton
from PySide6.QtWidgets import QMessageBox, QProgressBar, QLineEdit

import config
import load_order_eps
import zpl as zpl_print
from MainMenu import MainMenu
from ModelSKU import ModelSKU
# from SetupWindow import SetupWindow
from ToolBar import ToolBar
from exceptions import LoadOrderEPSError


# TODO: изменить курсор при загрузке

# TODO: Запустить прогресс-бар

# TODO: Сделать выбор типа этикетки автоматически


class LoadFileDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Загрузка кодов из файла")
        self.resize(300, 100)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Загрузка кодов из файла"))
        self.setLayout(layout)


# noinspection PyPep8Naming
class LoadEPSThread(QThread):
    finished = Signal()

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self):
        load_order_eps.process_zip(self.filename)

        self.finished.emit()


class ThreadCodJpgDecode(QThread):
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

    # def run(self):
    #     app_dir = cv.appDir
    #     source_filename = self.fileName
    #
    #     self.fileList = os.listdir(cv.tmpDir)
    #     for file in self.fileList:
    #         fullFileName = cv.tmpDir + file
    #         os.remove(fullFileName)
    #     self.convert_pdf2img(self.fileName)
    #     self.fileList = os.listdir(cv.tmpDir)
    #     self.signalStart.emit(len(self.fileList))
    #     defectCodeCount: int = 0
    #     dict_filename = {}
    #
    #     k = 0
    #     for f in self.fileList:
    #         filename = cv.tmpDir + f
    #         # c:\PythonProject\printQR-CodGoDEX\tmp\
    #         # файлы с картинками по 20 шт
    #         img = ImagePIL.open(filename)
    #         for i in range(20):
    #             k += 1
    #             print(k)
    #             # получаем по индексу координаты одного кода
    #             crop_img = img.crop(QR_IN_1[i])
    #             # сохранияем картинку на диск
    #             crop_img.save(f'{cv.imgTempDir}crop_img{k}.png')
    #             # запоминиаем имя файла
    #             filename = f'{cv.imgTempDir}crop_img{k}.png'
    #             print(filename)
    #             # распознаем код из картинки
    #             # data = decode(crop_img)
    #             # проверяем наличие кода
    #             if True:  # len(data) > 0 and data:
    #                 # сохранием код
    #                 cod = '0'  # data[0].data
    #                 # создаем словарь
    #                 dict_filename[cod] = filename
    #             # else:
    #             #     defectCodeCount += 1
    #         self.signalExec.emit()
    #
    #     try:
    #         cv.tempDir = shutil.move(source_filename, cv.tempDir)
    #         print("File is moved successfully to: ", cv.tempDir)
    #     except IsADirectoryError:
    #         print("Source is a file but destination is a directory.")
    #     except NotADirectoryError:
    #         print("Source is a directory but destination is a file.")
    #     except PermissionError:
    #         print("Operation not permitted.")
    #     except OSError as error:
    #         print(error)
    #
    #     dateToday = date.today().strftime('%d.%m.%Y')
    #     list_cod_to_BD = []
    #     for key, value in dict_filename.items():
    #         with open(value, 'rb') as file:
    #             blob_data = file.read()
    #         str_list_cod = (self.id_sku, key, 0, 0, dateToday, blob_data)
    #         list_cod_to_BD.append(str_list_cod)
    #
    #     con = sl.connect('SFMDEX.db')
    #     cur = con.cursor()
    #     sql = '''INSERT INTO codes(id_sku, cod, print, id_party, date_load, cod_img) values(?,?,?,?,?,?)'''
    #     cur.executemany(sql, list_cod_to_BD)
    #     sql = f'''INSERT INTO file_load (name) values("{self.fn}")'''
    #     cur.execute(sql)
    #     con.commit()
    #     con.close()
    #     self.signalFinished.emit(len(list_cod_to_BD), defectCodeCount)

    # @staticmethod
    # def convert_pdf2img(filename: str):
    #     """Преобразует PDF в изображение и создает файл за страницей"""
    #     pdf_in = fitz.open(filename)
    #     i = 0
    #     mat = fitz.Matrix(4, 4)
    #     for page in pdf_in:
    #         i += 1
    #         output_file = os.getcwd() + "\\tmp\\order" + str(i) + ".jpg"
    #         pix = page.get_pixmap(matrix=mat)
    #         pix.save(output_file)
    #     pdf_in.close()


# noinspection PyPep8Naming
class ModelSelectGroup(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refreshSelectGroup()

    def refreshSelectGroup(self):
        sql = 'SELECT name, id FROM groups ORDER BY sort'
        self.setQuery(sql)


# noinspection PyPep8Naming
class ModelSelectCompany(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refreshSelectCompany()

    def refreshSelectCompany(self):
        sql = 'SELECT name, id FROM company ORDER BY id'
        self.setQuery(sql)


# noinspection PyPep8Naming
class LoadFileEPS:
    pass


class MainWindow(QMainWindow):
    select_label = config.SELECT_LABEL

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Молочное море/Биорич - PrintDM - GoDEX530 - {config.VERSION}')
        self.resize(800, 700)
        self.dlg = None
        self.countProgress = 0
        self.codes = []
        self.id_company = None
        self.id_groups = None
        self.LabelType = ''
        self.PrinterControl = ''
        self.selectIdTableView = 0

        main_menu = MainMenu(self)
        main_menu.load_file.triggered.connect(self.load_file_triggered)
        main_menu.load_file_two.triggered.connect(self.load_file_two_triggered)
        main_menu.load_file_eps.triggered.connect(self.load_file_eps_triggered)
        # main_menu.setup.triggered.connect(self.setupDialog_triggered)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        tool_bar.load_file.triggered.connect(self.load_file_triggered)
        tool_bar.load_file_two.triggered.connect(self.load_file_two_triggered)
        tool_bar.load_file_eps.triggered.connect(self.load_file_eps_triggered)
        # tool_bar.setup.triggered.connect(self.setupDialog_triggered)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        layV = QVBoxLayout()
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(False)

        self.tvSKU = QTableView()
        self.modelSKU = ModelSKU()
        self.tvSKU.setModel(self.modelSKU)
        self.tvSKU.setSelectionBehavior(self.tvSKU.SelectionBehavior.SelectRows)
        self.refreshSKU()
        self.tvSKU.clicked.connect(self.tvSKU_clicked)

        self.strTableViewSelect = 'Строка таблицы:'
        self.lblSelectIdTableView = QLabel()
        self.lblSelectIdTableView.setText(self.strTableViewSelect)

        layHSelectIdTableView = QHBoxLayout()
        layHSelectIdTableView.addWidget(self.lblSelectIdTableView)

        lblDate = QLabel('Дата: ')
        self.deDate = QDateEdit()
        self.deDate.setMinimumWidth(150)
        self.deDate.setDate(date.today())
        self.deDate.setDisplayFormat('dd.MM.yyyy')
        self.deDate.setCalendarPopup(True)

        lblParty = QLabel('Партия: ')
        self.leParty = QLineEdit()
        self.leParty.setPlaceholderText('Введите номер партии')

        lblCount = QLabel('Количество: ')
        self.sbCount = QSpinBox()
        self.sbCount.setValue(1)
        self.sbCount.setMaximum(999)
        self.sbCount.setMinimumWidth(100)

        layHDateDate = QHBoxLayout()
        layHDateDate.addWidget(lblDate)
        layHDateDate.addWidget(self.deDate)
        layHDateDate.addWidget(lblParty)
        layHDateDate.addWidget(self.leParty)
        layHDateDate.addWidget(lblCount)
        layHDateDate.addWidget(self.sbCount)
        layHDateDate.setAlignment(Qt.AlignmentFlag.AlignLeft)

        btnPrint = QPushButton('Печать')
        btnPrint.clicked.connect(self.btnPrint_clicked)

        lblSelectTypeLabel = QLabel('Выберите тип этикетки: ')
        self.cbSelectTypeLabel = QComboBox()
        self.cbSelectTypeLabel.addItem('Выберите тип этикетки')
        self.cbSelectTypeLabel.addItems(self.select_label.keys())
        layHLabelSelectPrinter = QHBoxLayout()
        layHLabelSelectPrinter.addWidget(lblSelectTypeLabel)
        layHLabelSelectPrinter.addWidget(self.cbSelectTypeLabel)
        layHLabelSelectPrinter.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layV.addWidget(self.progressBar)
        layV.addWidget(self.tvSKU)
        layV.addLayout(layHSelectIdTableView)
        layV.addLayout(layHDateDate)
        layV.addLayout(layHLabelSelectPrinter)
        layV.addWidget(btnPrint)
        layV.setAlignment(Qt.AlignmentFlag.AlignTop)

        container = QWidget()
        container.setLayout(layV)
        self.centralWidget()
        self.setCentralWidget(container)

        # self.readConfigINI()
        self._createContextMenuTableSKU()
        self.modelSKU.modelRefreshSKU()

    def _createContextMenuTableSKU(self):
        print('_createContextMenuTableSKU')
        self.tvSKU.setContextMenuPolicy(Qt.ActionsContextMenu)
        copyGtinAction = QAction('копировать GTIN', self)
        copyGtinAction.triggered.connect(self.copyGtinAction)
        self.tvSKU.addAction(copyGtinAction)

    # noinspection PyPep8Naming
    def tvSKU_clicked(self, index: QModelIndex):
        """
        Проверка изменения строки таблицы.
        При изменении - обнуление номера партии.
        """
        row = index.row()
        if not self.selectIdTableView == row:
            self.selectIdTableView = row
            self.leParty.setText('')
            GTIN = self.tvSKU.model().index(row, 0).data()
            name = self.tvSKU.model().index(row, 1).data()
            self.lblSelectIdTableView.setText(f'{self.strTableViewSelect} GTIN - {GTIN}, наименование - {name}')

    def copyGtinAction(self):
        print('copyGtinAction')
        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(selectGTIN)

    # def readConfigINI(self):
    #     config = configparser.ConfigParser()
    #     config.read('setting.ini')
    #     default = config['DEFAULT']
    #     self.LabelType = default['LabelType']
    #     self.lblSelectTypeLabels = self.LabelType
    #     print(f'self.lblSelectTypeLabels = {self.lblSelectTypeLabels}')
    #     self.PrinterControl = default['PrinterControl']

    # def setupDialog_triggered(self):
    #     dlg = SetupWindow()
    #     dlg.exec()
    #     self.readConfigINI()

    @staticmethod
    def checking_loads_file(filename: str) -> bool:
        """
        Checking availability of a file with codes for printing in the database.
        Проверка наличия файла с кодами для печати в базе данных.
        Args:
            filename (str): The name of the file with codes.
            имя файла с кодами.
        Returns:
            bool: True if the file is not in the database, False otherwise.
            Значение True, если файла нет в базе данных, в противном случае значение False.
        """
        try:
            with sl.connect('SFMDEX.db') as con:
                cur = con.cursor()

                cur.execute('SELECT count(id) FROM file_load WHERE name = ?', (filename,))
                return cur.fetchone()[0] == 0
        except sl.Error as e:
            logging.error(f'Ошибка при при проверке имени загружаемого файла: {e}')
            return False

    @staticmethod
    def save_name_load_file(filename: str) -> None:
        try:
            with sl.connect('SFMDEX.db') as con:
                cur = con.cursor()
                cur.execute('INSERT INTO file_load (name) VALUES (?)', (filename,))
        except sl.Error as e:
            logging.error(f'Ошибка при записи в таблицу "file_load": {e}')

    def load_file_eps_triggered(self):
        app_dir = os.getcwd()
        dir_load = f'{app_dir}'
        filename: str = QFileDialog.getOpenFileName(self, 'Открыть файл', dir_load, 'ZIP files (*.zip)')[0]
        if not self.checking_loads_file(filename):
            QMessageBox.warning(self, 'Внимание', 'Файл уже загружен')
            return
        self.setCursor(Qt.CursorShape.BusyCursor)

        self.setEnabled(False)
        try:
            load_order_eps.process_zip(filename)
            self.save_name_load_file(filename)
            self.modelSKU.modelRefreshSKU()
            QMessageBox.information(self, 'Внимание', 'Загрузка кодов прошла успешно')
        except LoadOrderEPSError as e:
            QMessageBox.critical(self, 'Внимание', f'{str(e)}: <br>Обратитесь к администратору')
            return
        finally:
            self.setEnabled(True)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def load_file_triggered(self):
        pass

    def load_file_two_triggered(self):
        app_dir = os.getcwd()
        dir_load = f'{app_dir}/dm'
        filename: str = QFileDialog.getOpenFileName(self, 'Открыть файл', dir_load, 'PDF files (*.pdf)')[0]
        if not filename:  # проверка на пустую строку
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

        self.threadOne = ThreadCodJpgDecode(filename, id_sku, fn)
        self.threadOne.signalStart.connect(self.threadStartOne)
        self.threadOne.signalExec.connect(self.threadExecOne)
        self.threadOne.signalFinished.connect(self.threadFinishedTwo)
        self.threadOne.finished.connect(self.threadFinishedOne)
        self.threadOne.start()
        source = f'{app_dir}/dm/{filename}'
        dest = f'{app_dir}/temp/{filename}'
        print(f'source={source}, dest={dest}')

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
        self.modelSKU.modelRefreshSKU()

    @QtCore.Slot()
    def threadFinishedTwo(self, codeCount, defectCodeCount):
        self.statusbar.showMessage(f'Загружено {codeCount}, забраковано {defectCodeCount}', 2500)

    # def cbBigDM_clicked(self):
    #     if self.cbBigDM.isChecked():
    #         self.cbBigDM.setText('Да')
    #     else:
    #         self.cbBigDM.setText('Нет')
    #     pass

    def btnPrint_clicked(self):
        """
        Основная функция для печати этикеток, управляющая процессом.
        """

        # Настройка логирования
        logging.basicConfig(level=logging.INFO)

        # Проверка ввода пользователя
        number_party, date_party, count_labels = self.validate_user_input()

        selected_key, selected_value, selectGTIN = self.get_selected_label_info()
        if not selected_value or not selectGTIN:
            return

        try:
            # Получение кодов для печати
            codes_bd, ids_to_update, id_sku, prefix = self.get_codes_for_printing(selectGTIN, count_labels)

            if not codes_bd:
                logging.warning("Не найдено кодов для печати.")
                return

            # Обновление статуса кодов в базе данных
            self.update_codes_status(ids_to_update)

            # Печать кодов
            for index, code in enumerate(codes_bd):
                code_dm = code[0].decode('utf-8')
                zpl = self.prepare_zpl(selected_value, code_dm, number_party, date_party, prefix, index+1)

                # Выбор принтера и печать
                match config.ACCESS_PRINTER:
                    case 'NETWORK':
                        self.print_on_network_printer(zpl)
                    case 'LOCAL':
                        self.print_on_local_printer(zpl)

        except sl.Error as e:
            logging.error(f"Ошибка работы с базой данных: {e}")
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
        finally:
            logging.info("Завершение работы функции.")
            self.modelSKU.modelRefreshSKU()

    def validate_user_input(self) -> tuple[None, None, int] | tuple[str, str, int]:
        """
        Проверяет ввод пользователя в графическом интерфейсе и возвращает номер и дату партии.
        Если данные некорректны, выводит сообщение и возвращает None.
        """
        if not self.leParty.text() and config.CHECKING_PARTY_INPUT:
            QMessageBox.information(self, 'Внимание', 'Введите номер партии')
            self.leParty.setFocus()
            return None, None, 1

        date_party = self.deDate.date().toString('dd.MM.yyyy')
        number_party = self.leParty.text()
        count_labels = self.sbCount.value()
        return number_party, date_party, count_labels

    def get_selected_label_info(self) -> Tuple[str, str, str]:
        """
        Получает информацию о выбранной этикетке и строке SKU.
        """
        selected_index = self.cbSelectTypeLabel.currentIndex()
        selected_key = self.cbSelectTypeLabel.currentText()

        if selected_index == 0:
            QMessageBox.critical(self, 'Внимание', 'Выберите тип этикетки для печати')
            return '', '', ''

        selected_value = self.select_label[selected_key]
        self.cbSelectTypeLabel.setCurrentIndex(0)

        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        if selectIndexTableSKU == -1:
            QMessageBox.information(self, 'Внимание', 'Выберите строку для печати')
            return '', '', ''

        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()
        return selected_key, selected_value, selectGTIN

    def get_codes_for_printing(self, selectGTIN: str, count_labels: int) -> tuple[list[Any], list[Any], None, None] | \
                                                                            tuple[list[Any], list[Any], Any, Any]:
        """
        Получает коды для печати и возвращает их вместе со списком ID для обновления.
        """
        try:
            with sl.connect('SFMDEX.db') as con:
                cur = con.cursor()

                # Получение SKU
                cur.execute('SELECT id, prefix FROM sku WHERE gtin = ?', (selectGTIN,))
                id_sku = cur.fetchone()
                if id_sku is None:
                    QMessageBox.information(self, 'Внимание', 'Товар не найден')
                    return [], [], None, None

                # Проверка доступности кодов
                cur.execute('SELECT COUNT(cod) FROM codes WHERE id_sku = ?', (id_sku[0],))
                record = cur.fetchone()
                if self.sbCount.value() > record[0]:
                    QMessageBox.information(self, 'Внимание', 'Загрузите коды, не хватает для печати')
                    return [], [], None, None

                # Получение кодов для печати
                cur.execute('''
                    SELECT cod, id FROM codes 
                    WHERE print = 0 AND id_sku = ? 
                    ORDER BY date_load 
                    LIMIT ?''', (id_sku[0], count_labels))
                codes_bd = cur.fetchall()

                # Формирование списка ID для обновления
                ids_to_update = [code[1] for code in codes_bd]
                print(id_sku[1])
                return codes_bd, ids_to_update, id_sku[0], id_sku[1]
        except sl.Error as e:
            logging.error(f"Ошибка при запросе данных из базы: {e}")
            return [], [], None, None

    @staticmethod
    def update_codes_status(ids_to_update: List[int]):
        """
        Обновляет статус кодов в базе данных.
        """
        try:
            with sl.connect('SFMDEX.db') as con:
                cur = con.cursor()

                cur.execute(f'''
                    UPDATE codes SET print = 1, date_output = ? 
                    WHERE id IN ({','.join(['?'] * len(ids_to_update))})''',
                            (datetime.now(), *ids_to_update))
                con.commit()
        except sl.Error as e:
            logging.error(f"Ошибка обновления кодов в базе данных: {e}")

    @staticmethod
    def prepare_zpl(selected_value: str, code_dm: str, number_party: str, date_party: str, prefix: str, index: int) -> str:
        """
        Подготавливает ZPL для печати в зависимости от типа этикетки.
        """
        match selected_value:
            case 'BT_small':
                zpl = (zpl_print.ZPL_BT_SMALL.replace('code', code_dm).replace('number_party', prefix).
                       replace('date_party', date_party).replace('sequence_number', str(index)))
            case 'MB_big':
                zpl = (zpl_print.ZPL_MB_BIG.replace('code', code_dm).replace('number_party', number_party).
                       replace('date_party', date_party))
            case 'LF_big':
                zpl = (zpl_print.ZPL_LF_BIG.replace('code', code_dm).replace('number_party', number_party).
                       replace('date_party', date_party))
            case 'ML_big':
                zpl = (zpl_print.ZPL_ML_BIG.replace('code', code_dm).replace('number_party', '').
                       replace('date_party', ''))
            case _:
                raise ValueError(f"Тип этикетки не поддерживается: {selected_value}")
        return zpl

    @staticmethod
    def print_on_network_printer(zpl: str):
        """
        Печатает этикетку на сетевом принтере.
        """
        printer_ip = "192.168.1.10"  # IP сетевого принтера
        printer_port = 9100

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((printer_ip, printer_port))
                s.sendall(zpl.encode('utf-8'))
                logging.info(f"Этикетка успешно отправлена на сетевой принтер.")
        except socket.error as e:
            logging.error(f"Ошибка при отправке на сетевой принтер: {e}")

    @staticmethod
    def print_on_local_printer(zpl: str):
        """
        Печатает этикетку на локальном принтере через win32print.
        """
        local_printer_name = config.PRINTER_NAME  # Имя локального принтера

        try:
            hPrinter = win32print.OpenPrinter(local_printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Label Print", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, zpl.encode('utf-8'))
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                logging.info(f"Этикетка успешно отправлена на локальный принтер {local_printer_name}.")
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            logging.error(f"Ошибка при печати на локальном принтере: {e}")

    @staticmethod
    def checkingFileUpload(filename):
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

    def cbSelectGroup_currentTextChanged(self, name):  # Выбор группы
        sql = f'SELECT id FROM groups WHERE name = "{name}"'
        query = QtSql.QSqlQuery()
        query.exec(sql)
        if query.isActive():
            query.first()
            id_groups = query.value('id')
            self.id_groups = id_groups
        self.modelSKU.modelRefreshSKU()

    # def cbSelectCompany_currentTextChanged(self, name):  # Выбор кампании
    #     id_company = 2
    #     sql = f'SELECT id FROM company WHERE name = "{name}"'
    #     query = QtSql.QSqlQuery()
    #     query.exec(sql)
    #     if query.isActive():
    #         query.first()
    #         id_company = query.value('id')
    #         self.id_company = id_company
    #     self.cbSelectGroup.setCurrentIndex(0)
    #     self.modelSKU.modelRefreshSKU()
