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
        self.LabelType = self.rbOnlyDMCod.toolTip()

        self.rbDMCodDatePartyNumber = QRadioButton('DM код + дата + партия + №')
        self.rbDMCodDatePartyNumber.setToolTip('DMCodDatePartyNumber')

        self.rbDMCodDate20x20 = QRadioButton('DM код + дата, 20х20')
        self.rbDMCodDate20x20.setToolTip('DMCodDate20x20')

        self.rbDMCodLactofera = QRadioButton('Lactofera+Metalakt')
        self.rbDMCodLactofera.setToolTip('DMCodLactofera')

        self.rdDMCodColostrum = QRadioButton('Colostrum')
        self.rdDMCodColostrum.setToolTip('DMCodColostrum')

        self.rdDMFoodMail = QRadioButton('FoodMail')
        self.rdDMFoodMail.setToolTip('DMFoodMail')

        self.btgLabelType = QButtonGroup()
        self.btgLabelType.addButton(self.rbOnlyDMCod)
        self.btgLabelType.addButton(self.rbDMCodDatePartyNumber)
        self.btgLabelType.addButton(self.rbDMCodDate20x20)
        self.btgLabelType.addButton(self.rbDMCodLactofera)
        self.btgLabelType.addButton(self.rdDMCodColostrum)
        self.btgLabelType.addButton(self.rdDMFoodMail)

        self.btgLabelType.buttonClicked.connect(self.btgLabelType_buttonClicked)

        layVLabelType = QVBoxLayout()
        layVLabelType.addWidget(lblCaptionLabelType)
        layVLabelType.addWidget(self.rbOnlyDMCod)
        layVLabelType.addWidget(self.rbDMCodDatePartyNumber)
        layVLabelType.addWidget(self.rbDMCodDate20x20)
        layVLabelType.addWidget(self.rbDMCodLactofera)
        layVLabelType.addWidget(self.rdDMCodColostrum)
        layVLabelType.addWidget(self.rdDMFoodMail)

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
        self.readConfigINI()

    def readConfigINI(self):
        config = configparser.ConfigParser()
        config.read('setting.ini')
        default = config['DEFAULT']
        LabelType = default['LabelType']
        match LabelType:
            case 'OnlyDMCod':
                self.rbOnlyDMCod.setChecked(True)
                self.rbDMCodDatePartyNumber.setChecked(False)
                self.rbDMCodDate20x20.setChecked(False)
                self.rbDMCodLactofera.setChecked(False)
                self.rdDMCodColostrum.setChecked(False)
                self.rdDMFoodMail.setChecked(False)
            case 'DMCodDatePartyNumber':
                self.rbDMCodDatePartyNumber.setChecked(True)
                self.rbOnlyDMCod.setChecked(False)
                self.rbDMCodDate20x20.setChecked(False)
                self.rbDMCodLactofera.setChecked(False)
                self.rdDMCodColostrum.setChecked(False)
                self.rdDMFoodMail.setChecked(False)
            case 'DMCodDate20x20':
                self.rbDMCodDate20x20.setChecked(True)
                self.rbOnlyDMCod.setChecked(False)
                self.rbDMCodDatePartyNumber.setChecked(False)
                self.rbDMCodLactofera.setChecked(False)
                self.rdDMCodColostrum.setChecked(False)
                self.rdDMFoodMail.setChecked(False)
            case 'DMCodLactofera':
                self.rbDMCodLactofera.setChecked(True)
                self.rbDMCodDate20x20.setChecked(False)
                self.rbOnlyDMCod.setChecked(False)
                self.rbDMCodDatePartyNumber.setChecked(False)
                self.rdDMCodColostrum.setChecked(False)
                self.rdDMFoodMail.setChecked(False)
            case 'DMCodColostrum':
                self.rdDMCodColostrum.setChecked(True)
                self.rbDMCodLactofera.setChecked(False)
                self.rbDMCodDate20x20.setChecked(False)
                self.rbOnlyDMCod.setChecked(False)
                self.rbDMCodDatePartyNumber.setChecked(False)
                self.rdDMFoodMail.setChecked(False)
            case 'DMFoodMail':
                self.rdDMFoodMail.setChecked(True)
                self.rdDMCodColostrum.setChecked(False)
                self.rbDMCodLactofera.setChecked(False)
                self.rbDMCodDate20x20.setChecked(False)
                self.rbOnlyDMCod.setChecked(False)
                self.rbDMCodDatePartyNumber.setChecked(False)

        PrinterControl = default['PrinterControl']
        index = self.cbSetupPrinter.findText(PrinterControl)
        self.cbSetupPrinter.setCurrentIndex(index)

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
