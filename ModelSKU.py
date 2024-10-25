from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQueryModel
import config


class ModelSKU(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelRefreshSKU()  # инициализация установка на первую организацию id = 1
        self.setHeaderData(0, Qt.Orientation.Horizontal, 'GTIN')
        self.setHeaderData(1, Qt.Orientation.Horizontal, 'Наименование')
        self.setHeaderData(2, Qt.Orientation.Horizontal, 'Количество')

    def modelRefreshSKU(self):
        sql = f'''SELECT gtin, name, COUNT(id_sku) as codes 
                    FROM sku LEFT OUTER JOIN codes 
                    ON (sku.id = codes.id_sku) 
                    WHERE sku.id_company = {config.COMPANY} AND codes.print = 0
                    GROUP BY name
        '''
        self.setQuery(sql)

