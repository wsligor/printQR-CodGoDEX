import sys
from Application import Application
from MainWindow import MainWindow


if __name__ == '__main__':
    app = Application(sys.argv)
    mn = MainWindow()
    mn.show()

    result = app.exec()
    sys.exit(result)