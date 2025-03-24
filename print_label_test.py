import unittest
from unittest.mock import patch, MagicMock

import sqlite3 as sl

from exceptions import PrintLabelError
from print_label import _get_prefix_for_printing, _calculate_check_digit, _is_valid_gtin, _print_on_local_printer
from print_label import _get_codes_for_printing


class TestGetPrefixForPrinting(unittest.TestCase):
    """
        Test _get_prefix_for_printing()
    """

    @patch('print_label._is_valid_gtin')  # Замените module_name на имя модуля, где определена функция
    @patch('print_label.sl.connect')  # Патчим подключение к базе данных
    def test_valid_gtin_with_existing_prefix(self, mock_connect, mock_is_valid_gtin):
        # Настройка mock-объектов для успешного выполнения запроса
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ['valid_prefix']

        # Вызов функции
        selectGTIN = '04620058160080'
        result = _get_prefix_for_printing(selectGTIN)

        # Проверка корректности вызова и результата
        mock_is_valid_gtin.assert_called_once_with(selectGTIN)
        mock_cursor.execute.assert_called_once_with('SELECT prefix FROM sku WHERE gtin = ?', (selectGTIN,))
        self.assertEqual(result, 'valid_prefix')

    @patch('print_label._is_valid_gtin')
    @patch('print_label.sl.connect')
    def test_valid_gtin_with_missing_prefix(self, mock_connect, mock_is_valid_gtin):
        # Настройка для случая, когда в базе данных нет prefix
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [None]  # prefix отсутствует

        selectGTIN = '04620058160080'

        # Проверяем, что выбрасывается исключение PrintLabelError
        with self.assertRaises(PrintLabelError) as context:
            _get_prefix_for_printing(selectGTIN)

        # Проверяем сообщение ошибки
        self.assertEqual(str(context.exception), 'SKU(GTIN) не найден')

    @patch('print_label._is_valid_gtin')
    @patch('print_label.sl.connect')
    def test_database_error(self, mock_connect, mock_is_valid_gtin):
        # Настройка для случая, когда возникает ошибка базы данных
        mock_connect.side_effect = sl.Error('Database connection error')

        selectGTIN = '04620058160080'

        # Проверяем, что выбрасывается исключение PrintLabelError
        with self.assertRaises(PrintLabelError) as context:
            _get_prefix_for_printing(selectGTIN)

        # Проверяем сообщение ошибки
        self.assertEqual(str(context.exception), 'Произошла ошибка при запросе данных из базы "prefix"')

    @patch('print_label._is_valid_gtin')
    @patch('print_label.sl.connect')
    def test_invalid_gtin(self, mock_connect, mock_is_valid_gtin):
        # Настройка mock-объекта _is_valid_gtin для выбрасывания исключения
        mock_is_valid_gtin.side_effect = ValueError('Invalid GTIN')

        selectGTIN = '04620058160080'

        # Проверяем, что исключение ValueError будет передано корректно
        with self.assertRaises(ValueError) as context:
            _get_prefix_for_printing(selectGTIN)

        self.assertEqual(str(context.exception), 'Invalid GTIN')


class TestCalculateCheckDigit(unittest.TestCase):

    def test_valid_gtin_with_correct_check_digit(self):
        # Тестирование корректного GTIN с правильной контрольной цифрой
        self.assertTrue(_calculate_check_digit("04620058160080"))  # Контрольная цифра 0

    def test_valid_gtin_with_incorrect_check_digit(self):
        # Тестирование корректного GTIN с неправильной контрольной цифрой
        self.assertFalse(_calculate_check_digit("04620058160081"))  # Неправильная контрольная цифра 1 вместо 0

    def test_gtin_with_check_digit_as_9(self):
        # Тестирование GTIN с контрольной цифрой 9
        self.assertTrue(_calculate_check_digit("12345678901217"))  # Контрольная цифра 9

    def test_gtin_with_check_digit_as_0(self):
        # Тестирование GTIN с контрольной цифрой 0
        self.assertTrue(_calculate_check_digit("00000000000000"))  # Контрольная цифра 0


class TestIsValidGtin(unittest.TestCase):

    @patch('print_label._calculate_check_digit')
    def test_gtin_with_incorrect_length(self, mock_calculate_check_digit):
        mock_calculate_check_digit.return_value = True
        with self.assertRaises(PrintLabelError) as context:
            _is_valid_gtin('123456789012')
        self.assertEqual(str(context.exception), 'GTIN не соответствует формату')

    @patch('print_label._calculate_check_digit')
    def test_gtin_with_non_digit_characters(self, mock_calculate_check_digit):
        mock_calculate_check_digit.return_value = True
        with self.assertRaises(PrintLabelError) as context:
            _is_valid_gtin('1234567890120a')
        self.assertEqual(str(context.exception), 'GTIN не является числом')

    @patch('print_label._calculate_check_digit')
    def test_gtin_with_incorrect_check_digit(self, mock_calculate_check_digit):
        mock_calculate_check_digit.return_value = False
        with self.assertRaises(PrintLabelError) as context:
            _is_valid_gtin('1234567890123')
        self.assertEqual(str(context.exception), 'GTIN не соответствует формату')


class TestPrintOnLocalPrinter(unittest.TestCase):
    @patch('win32print.OpenPrinter')
    @patch('win32print.StartDocPrinter')
    @patch('win32print.StartPagePrinter')
    @patch('win32print.WritePrinter')
    @patch('win32print.EndPagePrinter')
    @patch('win32print.EndDocPrinter')
    @patch('win32print.ClosePrinter')
    @patch('config.PRINTER_NAME', 'TestPrinter')  # Имя принтера для теста
    def test_successful_print(self, mock_ClosePrinter, mock_EndDocPrinter, mock_EndPagePrinter,
                              mock_WritePrinter, mock_StartPagePrinter, mock_StartDocPrinter, mock_OpenPrinter):
        # Настраиваем мок на возвращаемое значение от OpenPrinter
        mock_OpenPrinter.return_value = MagicMock()  # Эмулируем дескриптор принтера

        # Вызов тестируемой функции
        _print_on_local_printer('^XA^FO50,50^ADN,36,20^FDHello, World!^FS^XZ')

        # Проверка, что все методы вызваны один раз
        mock_OpenPrinter.assert_called_once_with('TestPrinter')
        mock_StartDocPrinter.assert_called_once()
        mock_StartPagePrinter.assert_called_once()
        mock_WritePrinter.assert_called_once_with(mock_OpenPrinter.return_value,
                                                  b'^XA^FO50,50^ADN,36,20^FDHello, World!^FS^XZ')
        mock_EndPagePrinter.assert_called_once()
        mock_EndDocPrinter.assert_called_once()
        mock_ClosePrinter.assert_called_once()

    @patch('win32print.OpenPrinter', side_effect=Exception("Failed to open printer"))
    @patch('config.PRINTER_NAME', 'TestPrinter')
    def test_open_printer_error(self, mock_OpenPrinter):
        # Логирование при ошибке
        with self.assertLogs(level='ERROR') as log:
            _print_on_local_printer('^XA^FO50,50^ADN,36,20^FDHello, World!^FS^XZ')
            self.assertIn("Ошибка при печати на локальном принтере: Failed to open printer", log.output[0])

    # @patch('win32print.OpenPrinter')
    # @patch('win32print.StartDocPrinter', side_effect=Exception("Failed to start doc printer"))
    # @patch('config.PRINTER_NAME', 'TestPrinter')
    # def test_start_doc_printer_error(self, mock_OpenPrinter, mock_StartDocPrinter):
    #     # Настраиваем мок для OpenPrinter, чтобы вернуть значение
    #     mock_OpenPrinter.return_value = MagicMock()
    #
    #     # Логирование при ошибке
    #     with self.assertLogs(level='ERROR') as log:
    #         _print_on_local_printer('^XA^FO50,50^ADN,36,20^FDHello, World!^FS^XZ')
    #         self.assertIn("Ошибка при печати на локальном принтере: Failed to start doc printer", log.output[0])
    #
    #     # Проверка, что OpenPrinter был вызван, а StartDocPrinter тоже вызван и выбросил ошибку
    #     mock_OpenPrinter.assert_called_once_with('TestPrinter')
    #     mock_StartDocPrinter.assert_called_once()


class TestGetCodesForPrinting(unittest.TestCase):

    @patch('sqlite3.connect')
    def test_successful_retrieval(self, mock_connect):
        mock_con = MagicMock()
        mock_con.cursor.return_value = MagicMock()
        mock_cur = mock_con.cursor.return_value
        mock_cur.execute.return_value = None
        mock_cur.fetchall.return_value = [(1, 1), (2, 2)]

        mock_connect.return_value = mock_con

        selectGTIN = '1234567890123'
        count_labels = 2

        codes_bd, ids_to_update = _get_codes_for_printing(selectGTIN, count_labels)

        self.assertEqual(codes_bd, [(1, 1), (2, 2)])
        self.assertEqual(ids_to_update, [1, 2])

    @patch('sqlite3.connect')
    def test_insufficient_codes(self, mock_connect):
        mock_con = MagicMock()
        mock_con.cursor.return_value = MagicMock()
        mock_cur = mock_con.cursor.return_value
        mock_cur.execute.return_value = None
        mock_cur.fetchall.return_value = [(1, 1)]

        mock_connect.return_value = mock_con

        selectGTIN = '1234567890123'
        count_labels = 2

        with self.assertRaises(PrintLabelError):
            _get_codes_for_printing(selectGTIN, count_labels)

    @patch('sqlite3.connect')
    def test_database_error(self, mock_connect):
        mock_con = MagicMock()
        mock_con.cursor.return_value = MagicMock()
        mock_cur = mock_con.cursor.return_value
        mock_cur.execute.side_effect = sl.Error('Mock database error')

        mock_connect.return_value = mock_con

        selectGTIN = '1234567890123'
        count_labels = 2

        with self.assertRaises(PrintLabelError):
            _get_codes_for_printing(selectGTIN, count_labels)

    def test_invalid_gtin(self):
        selectGTIN = 'invalid_gtin'
        count_labels = 2

        with self.assertRaises(PrintLabelError):
            _get_codes_for_printing(selectGTIN, count_labels)

    def test_invalid_count_labels(self):
        """
        Test that _get_codes_for_printing raises a PrintLabelError
        when the count_labels parameter is negative.

        This test verifies that the function correctly handles
        invalid input by raising an exception for negative label counts.
        """
        selectGTIN = '1234567890123'
        count_labels = -1

        with self.assertRaises(PrintLabelError):
            _get_codes_for_printing(selectGTIN, count_labels)


if __name__ == '__main__':
    unittest.main()
