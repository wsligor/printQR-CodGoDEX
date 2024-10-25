from PySide6 import QtSql
from PySide6.QtWidgets import QApplication, QMessageBox

import config


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.DataBase = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.DataBase.setDatabaseName(config.DATABASE_NAME)
        print('BD')
        if not self.DataBase.open():
            QMessageBox.critical('Внимание', 'Ошибка подключения к БД')