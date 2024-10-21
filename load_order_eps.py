# Модуль для загрузки заказов из zip-файла с EPS-файлами
import json
import os
import zipfile
import sqlite3
import time
import logging
from PIL import Image
from datetime import datetime
from pylibdmtx.pylibdmtx import decode

from exceptions import LoadOrderEPSError

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def _profiler(func):
    def wrapper(*args, **kwargs):
        before = time.time()
        retval = func(*args, **kwargs)
        after = time.time()
        logging.debug("Function '%s': %s", func.__name__, after-before)

    return wrapper


# noinspection PyShadowingNames
# Адаптер для преобразования datetime в строку
def _adapt_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


# Конвертер для преобразования строки в datetime
def _convert_datetime(s):
    return datetime.strptime(s.decode('utf-8'), '%Y-%m-%d %H:%M:%S')


# Регистрация адаптера и конвертера
sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_converter('DATETIME', _convert_datetime)


def _check_paths(db_path: str, input_zip_path: str) -> None:
    # Check if input_zip_path and db_path exist
    if not os.path.exists(input_zip_path):
        raise ValueError(f"Invalid input_zip_path: {input_zip_path}")
    if not os.path.exists(db_path):
        raise ValueError(f"Invalid db_path: {db_path}")


def _extract_zip(input_zip_path: str, extract_to: str) -> None:
    # Extract all EPS files from the ZIP
    try:
        with zipfile.ZipFile(input_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    except Exception as e:
        raise ValueError(f"Failed to extract ZIP: {e}")


# @profiler
def _convert_eps_to_png(input_eps_path, output_png_path, resolution=300):
    with Image.open(input_eps_path) as img:
        img.load(scale=resolution // 72)  # 72 is the default resolution for EPS files
        img.save(output_png_path, 'PNG')


def _decode_datamatrix(image_path: str) -> str:
    """
    Decode the DataMatrix barcode from an image file.

    Args:
        image_path (str): The path to the image file.

    Returns:
        Optional[str]: The decoded data from the DataMatrix barcode, or None if no barcode is found.
    """
    with Image.open(image_path) as image:
        decoded_objects = decode(image)
        if decoded_objects:
            return decoded_objects[0].data
    return ''


def _insert_code(db_path, code, sku):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO codes (cod, print, date_load, id_sku) VALUES (?, ?, ?, ?)',
                   (code, 0, datetime.now(), sku))
    conn.commit()
    conn.close()


def _process_eps_files(db_path, sku_id, temp_dir):
    # Process each EPS file

    for file_name in os.listdir(temp_dir):
        if file_name.lower().endswith('.eps'):
            eps_path = os.path.join(temp_dir, file_name)
            png_path = os.path.join(temp_dir, file_name + '.png')

            # Convert EPS to PNG
            try:
                _convert_eps_to_png(eps_path, png_path)
            except Exception as e:
                raise ValueError(f"Failed to convert EPS to PNG: {e}")

            # Decode DataMatrix code from PNG
            try:
                code = _decode_datamatrix(png_path)
                if code:
                    _insert_code(db_path, code, sku_id)
            except Exception as e:
                raise ValueError(f"Failed to decode DataMatrix code: {e}")


def _clean_up(temp_dir: str) -> None:
    # Clean up temporary files
    for file_name in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file_name)
        try:
            os.remove(file_path)
        except Exception as e:
            raise ValueError(f"Failed to remove file: {e}")
    # try:
    #     os.rmdir(temp_dir)
    # except Exception as e:
    #     raise ValueError(f"Failed to remove directory: {e}")

def _check_attributes_json_file(temp_dir: str) -> bool:
    # Check if the attributes.json file exists
    fn = os.path.join(temp_dir, 'attributes.json')
    return os.path.exists(fn)


def _get_sku(temp_dir: str) -> str:
    # Get the SKU from the temporary directory
    fn = os.path.join(temp_dir, 'attributes.json')
    if not os.path.exists(fn):
        return ''
    with open(fn, 'r', encoding='utf-8') as f:
        data = json.load(f)
    keys = data['gtinProductAttributes'].keys()
    key = list(keys)[0]
    return key


def _get_sku_id(sku: str) -> int:
    # Get the SKU ID from the database
    #  TODO Проверить существование gtin в базе
    conn = sqlite3.connect('SFMDEX.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM sku WHERE gtin = ?', (sku,))
    row = cursor.fetchone()
    conn.close()
    return row[0]

def process_zip(input_zip_path: str, db_path: str, temp_dir: str = 'temp') -> None:
    """
    Process EPS files in a ZIP folder.
    Args:
        input_zip_path (str): Path to the ZIP file.
        db_path (str): Path to the database.
        temp_dir (str, optional): Temporary directory. Defaults to 'temp'.
    """
    try:
        _check_paths(db_path, input_zip_path)

        _extract_zip(input_zip_path, temp_dir)

        # TODO Разобраться с исключениями
        if _get_sku(temp_dir) == '':
            raise LoadOrderEPSError('SKU not found in attributes.json')
        else:
            sku = _get_sku(temp_dir)

        sku_id = _get_sku_id(sku)

        # Create the database and table if not exists
        # create_database(db_path)

        _process_eps_files(db_path, sku_id, temp_dir)

        _clean_up(temp_dir)
    except LoadOrderEPSError as e:
        raise LoadOrderEPSError(f"Failed to process ZIP: {e}")


# Example usage:
if __name__ == '__main__':
    input_zip_path = 'input.zip'  # Path to the input ZIP file with EPS files
    db_path = 'SFMDEX.db'  # Path to the SQLite database file
    # sku = '099'  # SKU KPD(КПД)
    # sku = '129'  # SKU Peptide Antiage A1
    process_zip(input_zip_path, db_path)
