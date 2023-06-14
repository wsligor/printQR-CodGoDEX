from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQueryModel


class ModelSKU(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelRefreshSKU()
        self.setHeaderData(0, Qt.Orientation.Horizontal, 'GTIN')
        self.setHeaderData(1, Qt.Orientation.Horizontal, 'Наименование')
        self.setHeaderData(2, Qt.Orientation.Horizontal, 'Количество')

    def modelRefreshSKU(self, id_groups=None, id_company=None):
        match id_groups:
            case id_groups if id_groups == None:
                sql = '''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes
                            ON (sku.id = codes.id_sku)
                            WHERE codes.print = 0                               
                            GROUP BY name
                '''
            case 17:
                sql = '''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes 
                            ON (sku.id = codes.id_sku) 
                            WHERE codes.print = 0
                            GROUP BY name
                '''
            case _:
                sql = f'''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes 
                            ON (sku.id = codes.id_sku) 
                            WHERE sku.id_groups = {id_groups} AND codes.print = 0
                            GROUP BY name
                '''
        self.setQuery(sql)
