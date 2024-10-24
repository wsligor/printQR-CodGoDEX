import unittest
from unittest.mock import patch, MagicMock

import sqlite3 as sl

from exceptions import PrintLabelError
from print_label import _get_prefix_for_printing, _calculate_check_digit, _is_valid_gtin


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


if __name__ == '__main__':
    unittest.main()
