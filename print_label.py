from dataclasses import dataclass
import logging
from datetime import datetime
import socket
import win32print
from typing import List
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
    prefix: str = ''


def print_label(options: OptionsPrintLabels) -> None:
    """
    Основная функция для печати этикеток, управляющая процессом.
    """

    # Настройка логирования
    logging.basicConfig(level=logging.INFO)

    try:
        # Получение кодов для печати
        options.prefix = _get_prefix_for_printing(options.gtin)
        codes_bd, ids_to_update = _get_codes_for_printing(options.gtin, options.count_labels)

        # Обновление статуса кодов в базе данных
        _update_codes_status(ids_to_update)

        # Печать кодов
        for i, code in enumerate(codes_bd):
            code_dm = code[0].decode('utf-8')
            zpl = _prepare_zpl(options, code_dm, str(i + 1))

            # Выбор принтера и печать
            match config.ACCESS_PRINTER:
                case 'NETWORK':
                    _print_on_network_printer(zpl)
                case 'LOCAL':
                    _print_on_local_printer(zpl)
                case 'NO PRINTING':
                    logging.info("Печать отключена.")
                    print(zpl)
                case _:
                    raise ValueError(f"Тип принтера не поддерживается: {config.ACCESS_PRINTER}")

    except sl.Error as e:
        logging.error(f"Ошибка работы с базой данных: {e}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
    finally:
        logging.info("Завершение работы функции.")


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

        with sl.connect(config.DATABASE_NAME) as con:
            cur = con.cursor()
            cur.execute('SELECT prefix FROM sku WHERE gtin = ?', (selectGTIN,))
            prefix = cur.fetchone()[0]
            if prefix is None:
                raise PrintLabelError('SKU(GTIN) не найден')
            return prefix
    except sl.Error as e:
        logging.error(f"Ошибка при запросе данных из базы: {e}")
        raise PrintLabelError('Произошла ошибка при запросе данных из базы "prefix"')


def _get_codes_for_printing(selectGTIN: str, count_labels: int):
    """
    Получает коды для печати и их ID.

    :param selectGTIN: GTIN для поиска соответствующих кодов SKU.
    :param count_labels: количество необходимых кодов для печати.
    :return: Кортеж, содержащий:
             - codes_bd: список кортежей с кодами для печати и их ID
             - ids_to_update: список ID для обновления статуса печати.
    :raises PrintLabelError: если кодов недостаточно или возникает ошибка базы данных.
    """
    try:
        if count_labels <= 0:
            raise PrintLabelError('Количество кодов для печати должно быть больше нуля')

        with sl.connect(config.DATABASE_NAME) as con:
            cur = con.cursor()

            # Проверка и получение кодов для печати
            cur.execute('''
                SELECT codes.cod, codes.id 
                FROM codes 
                JOIN sku ON sku.id = codes.id_sku 
                WHERE sku.gtin = ? AND codes.print = 0
                ORDER BY date_load
                LIMIT ?''', (selectGTIN, count_labels))

            codes_bd = cur.fetchall()

            # Проверка доступности требуемого количества кодов
            if len(codes_bd) < count_labels:
                raise PrintLabelError('Недостаточно кодов для печати')

            # Формирование списка ID для обновления
            ids_to_update = [code[1] for code in codes_bd]
            return codes_bd, ids_to_update
    except sl.Error as e:
        logging.error(f"Ошибка при запросе данных из базы: {e}")
        raise PrintLabelError('Произошла ошибка при запросе данных из базы')


def _update_codes_status(ids_to_update: List[int]):
    """
    Обновляет статус кодов в базе данных.
    """
    try:
        with sl.connect(config.DATABASE_NAME) as con:
            cur = con.cursor()

            sql = f'''
                UPDATE codes SET print = 1, date_output = ? 
                WHERE id IN ({','.join(['?'] * len(ids_to_update))})'''

            cur.execute(sql, (datetime.now(), *ids_to_update))
            con.commit()
    except sl.Error as e:
        logging.error(f"Ошибка обновления кодов в базе данных: {e}")
        raise PrintLabelError('Произошла ошибка при обновлении кодов в базе данных')


def _prepare_zpl(options: OptionsPrintLabels, code_dm: str, index: str) -> str:
    """
    Подготавливает ZPL для печати в зависимости от типа этикетки.
    """
    match options.type_labels:
        case 'BT_small':
            zpl = zpl_print.ZPL_BT_SMALL.format(code=code_dm,
                                                prefix=options.prefix,
                                                date_party=options.date_party,
                                                sequence_number=str(index))
        case 'MB_big':
            zpl = zpl_print.ZPL_MB_BIG.format(code=code_dm,
                                              number_party=options.number_party,
                                              date_party=options.date_party)
        case 'LF_big':
            zpl = zpl_print.ZPL_LF_BIG.format(code=code_dm,
                                              number_party=options.number_party,
                                              date_party=options.date_party)
        case 'ML_big':
            zpl = zpl_print.ZPL_ML_BIG.format(code=code_dm,
                                              number_party=options.number_party,
                                              date_party=options.date_party)
        case 'LF_box':
            zpl = zpl_print.ZPL_LF_BOX.format(code=code_dm,
                                              number_party=options.number_party,
                                              date_party=options.date_party)
        case _:
            raise ValueError(f"Тип этикетки не поддерживается: {options.type_labels}")
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


def _print_on_local_printer(zpl: str) -> None:
    """
    Печатает этикетку на локальном принтере через win32print.
    """
    local_printer_name = config.PRINTER_NAME  # Имя локального принтера
    hPrinter = None

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
            if hPrinter:
                win32print.ClosePrinter(hPrinter)
    except Exception as e:
        logging.error(f"Ошибка при печати на локальном принтере: {e}")


if __name__ == '__main__':
    # options = OptionsPrintLabels(
    #     gtin='04680147350083',
    #     number_party='456',
    #     date_party='01.01.2024',
    #     count_labels=1,
    #     type_labels='BT_small'
    # )
    # print_label(options)
    print(_get_prefix_for_printing('04680147350082'))
    # print(_get_codes_for_printing('04680147350082', 1))
