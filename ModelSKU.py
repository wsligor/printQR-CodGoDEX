from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQueryModel


class ModelSKU(QSqlQueryModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.modelRefreshSKU(1, id_groups=None) # инициализация установка на первую организацию id = 1
        self.setHeaderData(0, Qt.Orientation.Horizontal, 'GTIN')
        self.setHeaderData(1, Qt.Orientation.Horizontal, 'Наименование')
        self.setHeaderData(2, Qt.Orientation.Horizontal, 'Количество')

    def modelRefreshSKU(self, id_company, id_groups=None):
        if id_company is None:
            id_company = 1
        match id_groups:
            case id_groups if id_groups == None:
                sql = f'''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes
                            ON (sku.id = codes.id_sku)
                            WHERE sku.id_company = {id_company} AND codes.print = 0                               
                            GROUP BY name
                '''
            case 17:
                sql = f'''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes 
                            ON (sku.id = codes.id_sku) 
                            WHERE sku.id_company = {id_company} AND codes.print = 0
                            GROUP BY name
                '''
            case _:
                sql = f'''SELECT gtin, name, COUNT(id_sku) as codes 
                            FROM sku LEFT OUTER JOIN codes 
                            ON (sku.id = codes.id_sku) 
                            WHERE sku.id_company = {id_company} AND sku.id_groups = {id_groups} AND codes.print = 0
                            GROUP BY name
                '''
        self.setQuery(sql)
