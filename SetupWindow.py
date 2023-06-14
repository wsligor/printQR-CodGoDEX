from PySide6 import QtPrintSupport
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QComboBox, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QRadioButton, QButtonGroup

import configparser

class SetupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.LabelType = ''

        self.setWindowTitle('Настройки')
        self.resize(300, 200)

        lblCaptionLabelType = QLabel('Выберите вид этикетки:')
        self.rbOnlyDMCod = QRadioButton('Только DM код')
        self.rbOnlyDMCod.setToolTip('OnlyDMCod')
        self.rbOnlyDMCod.setChecked(True)
        self.LabelType = self.rbOnlyDMCod.toolTip()

        self.rbDMCodDatePartyNumber = QRadioButton('DM код + дата + партия + №')
        self.rbDMCodDatePartyNumber.setToolTip('DMCodDatePartyNumber')

        self.btgLabelType = QButtonGroup()
        self.btgLabelType.addButton(self.rbOnlyDMCod)
        self.btgLabelType.addButton(self.rbDMCodDatePartyNumber)

        self.btgLabelType.buttonClicked.connect(self.btgLabelType_buttonClicked)

        layVLabelType = QVBoxLayout()
        layVLabelType.addWidget(lblCaptionLabelType)
        layVLabelType.addWidget(self.rbOnlyDMCod)
        layVLabelType.addWidget(self.rbDMCodDatePartyNumber)

        lblSetupPrinter = QLabel('Выберите принтер для контроля:')
        self.cbSetupPrinter = QComboBox()
        self.cbSetupPrinter.addItems(QtPrintSupport.QPrinterInfo.availablePrinterNames())
        layVSetupPrinter = QVBoxLayout()
        layVSetupPrinter.addWidget(lblSetupPrinter)
        layVSetupPrinter.addWidget(self.cbSetupPrinter)

        btnOk = QPushButton('Ok')
        btnCancel = QPushButton('Cancel')
        btnCancel.clicked.connect(self.reject)
        btnOk.clicked.connect(self.btnOk_clicked)

        layHButton = QHBoxLayout()
        layHButton.addWidget(btnOk)
        layHButton.addWidget(btnCancel)
        layHButton.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.spaceItem = QSpacerItem(20, 40, QSizePolicy.Expanding)

        layV = QVBoxLayout(self)
        layV.setAlignment(Qt.AlignmentFlag.AlignTop)
        layV.addLayout(layVLabelType)
        layV.addSpacing(10)
        layV.addLayout(layVSetupPrinter)
        layV.addSpacerItem(self.spaceItem)
        layV.addLayout(layHButton)

        self.setLayout(layV)


    def btgLabelType_buttonClicked(self, btn):
        print(btn.toolTip())
        self.LabelType = btn.toolTip()

    def btnOk_clicked(self):
        print('btnOk_clicked')
        config = configparser.ConfigParser()
        default = config['DEFAULT']
        default['LabelType'] = self.LabelType
        default['PrinterControl'] = self.cbSetupPrinter.currentText()
        with open('setting.ini', 'w') as configfile:
            config.write(configfile)
        self.accept()