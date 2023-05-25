from PySide6 import QtSql
from PySide6.QtWidgets import QApplication, QMessageBox


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.DataBase = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.DataBase.setDatabaseName('SFMDEX.db')
        print('BD')
        if not self.DataBase.open():
            QMessageBox.critical('Внимание', 'Ошибка подключения к БД')