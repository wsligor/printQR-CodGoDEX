from dataclasses import dataclass
import logging
from datetime import datetime
import socket
import win32print
from typing import List, NamedTuple
import sqlite3 as sl

import zpl as zpl_print
import config
from exceptions import PrintLabelError


@dataclass
class OptionsPrintLabels:
    gtin: str
    number_party: str
    date_party: str
    count_labels: int
    type_labels: str


def print_label(options: OptionsPrintLabels) -> None:
    """
    Основная функция для печати этикеток, управляющая процессом.
    """

    # Настройка логирования
    logging.basicConfig(level=logging.INFO)

    try:
        # Получение кодов для печати
        prefix = _get_prefix_for_printing(options.gtin)
        codes_bd, ids_to_update = _get_codes_for_printing(options.gtin, options.count_labels)

        if not codes_bd:
            logging.warning("Не найдено кодов для печати.")
            return

        # Обновление статуса кодов в базе данных
        _update_codes_status(ids_to_update)

        # Печать кодов
        for i, code in enumerate(codes_bd):
            code_dm = code[0].decode('utf-8')
            zpl = _prepare_zpl(options.type_labels, code_dm, options.number_party, options.date_party, prefix, i + 1)

            # Выбор принтера и печать
            match config.ACCESS_PRINTER:
                case 'NETWORK':
                    _print_on_network_printer(zpl)
                case 'LOCAL':
                    _print_on_local_printer(zpl)
                case 'NO PRINTING':
                    logging.info("Печать отключена.")
                case _:
                    raise ValueError(f"Тип принтера не поддерживается: {config.ACCESS_PRINTER}")

    except sl.Error as e:
        logging.error(f"Ошибка работы с базой данных: {e}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        logging.info("Завершение работы функции.")


# Проверка контрольной суммы
def _calculate_check_digit(gtin: str) -> int:
    """
    Рассчитывает контрольную цифру для GTIN по алгоритму Луна.

    :param gtin: GTIN без контрольной цифры, строка из 13 цифр
    :return: контрольная цифра, целое число
    """
    gtin_codes = [int(digit) for digit in gtin[:-1]]  # Преобразуем все, кроме последней цифры, в список чисел
    total_sum = sum(gtin_codes[0::2]) * 3 + sum(gtin_codes[1::2])  # Сумма цифр с четных и нечетных позиций
    check_digit_calculate = (10 - (total_sum % 10)) % 10  # Вычисление контрольной цифры
    check_digit = int(gtin[-1])
    return check_digit_calculate == check_digit


def _is_valid_gtin(gtin: str) -> None:
    """
    Проверяет GTIN на соответствие формату.
    :param gtin: GTIN без контрольной цифры, строка из 13 цифр
    :return: True, если GTIN соответствует формату, False в противном случае
    """
    if len(gtin) != 14:
        raise PrintLabelError('GTIN не соответствует формату')
    if not gtin.isdigit():
        raise PrintLabelError('GTIN не является числом')
    if not _calculate_check_digit(gtin):
        raise PrintLabelError('GTIN не соответствует формату')


def _get_prefix_for_printing(selectGTIN) -> str:
    """
    Получает префикс для печати.
    :param selectGTIN:
    :return prefix:
    """
    _is_valid_gtin(selectGTIN)
    try:

        with sl.connect('SFMDEX.db') as con:
            cur = con.cursor()
            cur.execute('SELECT prefix FROM sku WHERE gtin = ?', (selectGTIN,))
            prefix = cur.fetchone()[0]
            if prefix is None:
                raise PrintLabelError('SKU(GTIN) не найден')
            return prefix
    except sl.Error as e:
        logging.error(f"Ошибка при запросе данных из базы: {e}")
        raise PrintLabelError('Произошла ошибка при запросе данных из базы "prefix"')


def _get_codes_for_printing(selectGTIN, count_labels):
    """
    Получает коды для печати и возвращает их вместе со списком ID для обновления.
    """
    try:
        with sl.connect('SFMDEX.db') as con:
            cur = con.cursor()

            # Получение SKU
            cur.execute('SELECT id, prefix FROM sku WHERE gtin = ?', (selectGTIN,))
            result = cur.fetchone()
            print(result)
            id_sku, prefix = result
            if id_sku is None:
                raise PrintLabelError('SKU(GTIN) не найден')

            # Проверка доступности кодов
            cur.execute('SELECT COUNT(cod) FROM codes WHERE id_sku = ?', (id_sku,))
            record = cur.fetchone()
            if count_labels > record[0]:
                raise PrintLabelError('Недостаточно кодов для печати')

            # Получение кодов для печати
            cur.execute('''
                SELECT cod, id FROM codes 
                WHERE print = 0 AND id_sku = ? 
                ORDER BY date_load 
                LIMIT ?''', (id_sku, count_labels))
            codes_bd = cur.fetchall()

            # Формирование списка ID для обновления
            ids_to_update = [code[1] for code in codes_bd]
            print(codes_bd, ids_to_update, prefix)
            return codes_bd, ids_to_update
    except sl.Error as e:
        logging.error(f"Ошибка при запросе данных из базы: {e}")
        raise PrintLabelError('Произошла ошибка при запросе данных из базы')


def _update_codes_status(ids_to_update: List[int]):
    """
    Обновляет статус кодов в базе данных.
    """
    try:
        with sl.connect('SFMDEX.db') as con:
            cur = con.cursor()

            sql = f'''
                UPDATE codes SET print = 1, date_output = ? 
                WHERE id IN ({','.join(['?'] * len(ids_to_update))})'''

            cur.execute(sql, (datetime.now(), *ids_to_update))
            con.commit()
    except sl.Error as e:
        logging.error(f"Ошибка обновления кодов в базе данных: {e}")


def _prepare_zpl(selected_value: str, code_dm: str, number_party: str, date_party: str, prefix: str,
                 index: int) -> str:
    """
    Подготавливает ZPL для печати в зависимости от типа этикетки.
    """
    match selected_value:
        case 'BT_small':
            zpl = (zpl_print.ZPL_BT_SMALL.replace('code', code_dm).replace('number_party', prefix).
                   replace('date_party', date_party).replace('sequence_number', str(index)))
        case 'MB_big':
            zpl = (zpl_print.ZPL_MB_BIG.replace('code', code_dm).replace('number_party', number_party).
                   replace('date_party', date_party))
        case 'LF_big':
            zpl = (zpl_print.ZPL_LF_BIG.replace('code', code_dm).replace('number_party', number_party).
                   replace('date_party', date_party))
        case 'ML_big':
            zpl = (zpl_print.ZPL_ML_BIG.replace('code', code_dm).replace('number_party', '').
                   replace('date_party', ''))
        case _:
            raise ValueError(f"Тип этикетки не поддерживается: {selected_value}")
    return zpl


def _print_on_network_printer(zpl: str):
    """
    Печатает этикетку на сетевом принтере.
    """
    printer_ip = "192.168.1.10"  # IP сетевого принтера
    printer_port = 9100

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((printer_ip, printer_port))
            s.sendall(zpl.encode('utf-8'))
            logging.info(f"Этикетка успешно отправлена на сетевой принтер.")
    except socket.error as e:
        logging.error(f"Ошибка при отправке на сетевой принтер: {e}")


def _print_on_local_printer(zpl: str):
    """
    Печатает этикетку на локальном принтере через win32print.
    """
    local_printer_name = config.PRINTER_NAME  # Имя локального принтера

    try:
        hPrinter = win32print.OpenPrinter(local_printer_name)
        try:
            win32print.StartDocPrinter(hPrinter, 1, ("Label Print", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, zpl.encode('utf-8'))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            logging.info(f"Этикетка успешно отправлена на локальный принтер {local_printer_name}.")
        finally:
            win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logging.error(f"Ошибка при печати на локальном принтере: {e}")


if __name__ == '__main__':
    options = OptionsPrintLabels(
        gtin='04680147350083',
        number_party='456',
        date_party='01.01.2024',
        count_labels=1,
        type_labels='BT_small'
    )
    # print_label(options)
    print(_get_prefix_for_printing('04680147350082'))
    # print(_get_codes_for_printing('04680147350082', 1))
