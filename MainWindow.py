import logging
import os
import sqlite3 as sl
from datetime import date
from typing import Tuple

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import QLabel, QStatusBar, QComboBox, QWidget, QVBoxLayout, QFileDialog, QDateEdit, QDialog
from PySide6.QtWidgets import QMainWindow, QTableView, QHeaderView, QHBoxLayout, QSpinBox, QPushButton
from PySide6.QtWidgets import QMessageBox, QProgressBar, QLineEdit

import config
import load_order_eps
import print_label

from MainMenu import MainMenu
from ModelSKU import ModelSKU
from ToolBar import ToolBar
from exceptions import LoadOrderEPSError, PrintLabelError



# TODO: Запустить прогресс-бар

# TODO: Сделать выбор типа этикетки автоматически

# TODO: Распределить файлы по каталогам для удобного обновления на локальных компьютерах


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
        main_menu.load_file_eps.triggered.connect(self.load_file_eps_triggered)
        self.setMenuBar(main_menu)
        tool_bar = ToolBar(parent=self)
        tool_bar.load_file_eps.triggered.connect(self.load_file_eps_triggered)
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

        self._createContextMenuTableSKU()
        self.modelSKU.modelRefreshSKU()

    def _createContextMenuTableSKU(self):
        self.tvSKU.setContextMenuPolicy(Qt.ActionsContextMenu)
        copyGtinAction = QAction('копировать GTIN', self)
        copyGtinAction.triggered.connect(self.copyGtinAction)
        self.tvSKU.addAction(copyGtinAction)

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
        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()

        clipboard = QGuiApplication.clipboard()
        clipboard.setText(selectGTIN)

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
            self.modelSKU.modelRefreshSKU()
            QMessageBox.information(self, 'Внимание', 'Загрузка кодов прошла успешно')
        except LoadOrderEPSError as e:
            QMessageBox.critical(self, 'Внимание', f'{str(e)}: <br>Обратитесь к администратору')
            return
        finally:
            self.setEnabled(True)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def btnPrint_clicked(self):
        selected_key, selected_value, selectGTIN = self.get_selected_label_info()
        number_party, date_party, count_labels = self.validate_user_input()
        options = print_label.OptionsPrintLabels(selectGTIN, number_party, date_party, count_labels, selected_value)
        try:
            print_label.print_label(options)
        except PrintLabelError as e:
            QMessageBox.critical(self, 'Внимание', f'{str(e)}: <br>Обратитесь к администратору')
        self.modelSKU.modelRefreshSKU()
        self.tvSKU.setFocus()

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
        # self.cbSelectTypeLabel.setCurrentIndex(0)

        selectIndexTableSKU = self.tvSKU.currentIndex().row()
        # if selectIndexTableSKU == -1 or selectIndexTableSKU == 0:
        if selectIndexTableSKU == -1:
            QMessageBox.information(self, 'Внимание', 'Выберите строку для печати')
            return '', '', ''

        selectGTIN = self.tvSKU.model().index(selectIndexTableSKU, 0).data()
        return selected_key, selected_value, selectGTIN

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

    def refreshSKU(self):
        hh = self.tvSKU.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hv = self.tvSKU.verticalHeader()
        hv.hide()
