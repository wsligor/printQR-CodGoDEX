import sys
from Application import Application
from MainWindow import MainWindow

# TODO Меню по правой клавише на таблице копировать gtin, наименование, префикс
# TODO Контроль уникальности кодов


if __name__ == '__main__':
    app = Application(sys.argv)
    mn = MainWindow()
    mn.show()

    result = app.exec()
    sys.exit(result)