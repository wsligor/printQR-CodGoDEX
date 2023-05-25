import os
import fitz
from typing import Tuple

from PIL import Image as ImagePIL
from PIL import ImageEnhance as ImageEnhancePIL

from pylibdmtx.pylibdmtx import decode
from pylibdmtx.pylibdmtx import encode

# from pylibdmtx.pylibdmtx import decode

# Настройки для 120 этикеток
# CROP_RESIZE_WIDTH = 60
# CROP_RESIZE_HEIGHT = 60

CROP_RESIZE_WIDTH = 40
CROP_RESIZE_HEIGHT = 40

TILED_SIZE = (4961, 6850)

QR_IN = (
    (38, 88, 170, 220), (248, 88, 380, 220), (458, 88, 590, 220), (668, 88, 798, 220), (880, 88, 1012, 220),
    (38, 446, 170, 578), (248, 446, 380, 578), (458, 446, 590, 578), (668, 446, 798, 578), (880, 446, 1012, 578),
    (38, 804, 170, 936), (248, 804, 380, 936), (458, 804, 590, 936), (668, 804, 798, 936), (880, 804, 1012, 936),
    (38, 1162, 170, 1294), (248, 1162, 380, 1294), (458, 1162, 590, 1294), (668, 1162, 798, 1294),
    (880, 1162, 1012, 1294)
)

SY = 295  # step Y
SX = 488  # step X
SPY = 205  # start position Y
SPX = 173  # start position X

QR_OUT_220 = (
    # 1-0
    (SPX, SPY), (SPX + SX, SPY), (SPX + SX * 2, SPY), (SPX + SX * 3, SPY), (SPX + SX * 4, SPY),
    (SPX + SX * 5, SPY), (SPX + SX * 6, SPY), (SPX + SX * 7, SPY), (SPX + SX * 8, SPY), (SPX + SX * 9, SPY),  # 1
    # 2-0
    (SPX, SPY + SY), (SPX + SX, SPY + SY), (SPX + SX * 2, SPY + SY), (SPX + SX * 3, SPY + SY), (SPX + SX * 4, SPY + SY),
    (SPX + SX * 5, SPY + SY), (SPX + SX * 6, SPY + SY), (SPX + SX * 7, SPY + SY), (SPX + SX * 8, SPY + SY),
    (SPX + SX * 9, SPY + SY),  # 2
    # 3-0
    (SPX, SPY + SY * 2), (SPX + SX, SPY + SY * 2), (SPX + SX * 2, SPY + SY * 2), (SPX + SX * 3, SPY + SY * 2),
    (SPX + SX * 4, SPY + SY * 2),
    (SPX + SX * 5, SPY + SY * 2), (SPX + SX * 6, SPY + SY * 2), (SPX + SX * 7, SPY + SY * 2),
    (SPX + SX * 8, SPY + SY * 2), (SPX + SX * 9, SPY + SY * 2),  # 3
    # 4-0
    (SPX, SPY + SY * 3), (SPX + SX, SPY + SY * 3), (SPX + SX * 2, SPY + SY * 3), (SPX + SX * 3, SPY + SY * 3),
    (SPX + SX * 4, SPY + SY * 3),
    (SPX + SX * 5, SPY + SY * 3), (SPX + SX * 6, SPY + SY * 3), (SPX + SX * 7, SPY + SY * 3),
    (SPX + SX * 8, SPY + SY * 3), (SPX + SX * 9, SPY + SY * 3),  # 4
    # 5-0
    (SPX, SPY + SY * 4), (SPX + SX, SPY + SY * 4), (SPX + SX * 2, SPY + SY * 4), (SPX + SX * 3, SPY + SY * 4),
    (SPX + SX * 4, SPY + SY * 4),
    (SPX + SX * 5, SPY + SY * 4), (SPX + SX * 6, SPY + SY * 4), (SPX + SX * 7, SPY + SY * 4),
    (SPX + SX * 8, SPY + SY * 4), (SPX + SX * 9, SPY + SY * 4),  # 5
    # 6-0
    (SPX, SPY + SY * 5), (SPX + SX, SPY + SY * 5), (SPX + SX * 2, SPY + SY * 5), (SPX + SX * 3, SPY + SY * 5),
    (SPX + SX * 4, SPY + SY * 5),
    (SPX + SX * 5, SPY + SY * 5), (SPX + SX * 6, SPY + SY * 5), (SPX + SX * 7, SPY + SY * 5),
    (SPX + SX * 8, SPY + SY * 5), (SPX + SX * 9, SPY + SY * 5),  # 6
    # 7-0
    (SPX, SPY + SY * 6), (SPX + SX, SPY + SY * 6), (SPX + SX * 2, SPY + SY * 6), (SPX + SX * 3, SPY + SY * 6),
    (SPX + SX * 4, SPY + SY * 6),
    (SPX + SX * 5, SPY + SY * 6), (SPX + SX * 6, SPY + SY * 6), (SPX + SX * 7, SPY + SY * 6),
    (SPX + SX * 8, SPY + SY * 6), (SPX + SX * 9, SPY + SY * 6),  # 7
    # 8-1
    (SPX, SPY + SY * 7 - 1), (SPX + SX, SPY + SY * 7 - 1), (SPX + SX * 2, SPY + SY * 7 - 1),
    (SPX + SX * 3, SPY + SY * 7 - 1), (SPX + SX * 4, SPY + SY * 7 - 1),
    (SPX + SX * 5, SPY + SY * 7 - 1), (SPX + SX * 6, SPY + SY * 7 - 1), (SPX + SX * 7, SPY + SY * 7 - 1),
    (SPX + SX * 8, SPY + SY * 7 - 1), (SPX + SX * 9, SPY + SY * 7 - 1),  # 8
    # 9-1
    (SPX, SPY + SY * 8 - 1), (SPX + SX, SPY + SY * 8 - 1), (SPX + SX * 2, SPY + SY * 8 - 1),
    (SPX + SX * 3, SPY + SY * 8 - 1), (SPX + SX * 4, SPY + SY * 8 - 1),
    (SPX + SX * 5, SPY + SY * 8 - 1), (SPX + SX * 6, SPY + SY * 8 - 1), (SPX + SX * 7, SPY + SY * 8 - 1),
    (SPX + SX * 8, SPY + SY * 8 - 1), (SPX + SX * 9, SPY + SY * 8 - 1),  # 9
    # 10-1
    (SPX, SPY + SY * 9 - 1), (SPX + SX, SPY + SY * 9 - 1), (SPX + SX * 2, SPY + SY * 9 - 1),
    (SPX + SX * 3, SPY + SY * 9 - 1), (SPX + SX * 4, SPY + SY * 9 - 1),
    (SPX + SX * 5, SPY + SY * 9 - 1), (SPX + SX * 6, SPY + SY * 9 - 1), (SPX + SX * 7, SPY + SY * 9 - 1),
    (SPX + SX * 8, SPY + SY * 9 - 1), (SPX + SX * 9, SPY + SY * 9 - 1),  # 10
    # 11-2
    (SPX, SPY + SY * 10 - 2), (SPX + SX, SPY + SY * 10 - 2), (SPX + SX * 2, SPY + SY * 10 - 2),
    (SPX + SX * 3, SPY + SY * 10 - 2), (SPX + SX * 4, SPY + SY * 10 - 2),
    (SPX + SX * 5, SPY + SY * 10 - 2), (SPX + SX * 6, SPY + SY * 10 - 2), (SPX + SX * 7, SPY + SY * 10 - 2),
    (SPX + SX * 8, SPY + SY * 10 - 2), (SPX + SX * 9, SPY + SY * 10 - 2),  # 11
    # 12-2
    (SPX, SPY + SY * 11 - 2), (SPX + SX, SPY + SY * 11 - 2), (SPX + SX * 2, SPY + SY * 11 - 2),
    (SPX + SX * 3, SPY + SY * 11 - 2), (SPX + SX * 4, SPY + SY * 11 - 2),
    (SPX + SX * 5, SPY + SY * 11 - 2), (SPX + SX * 6, SPY + SY * 11 - 2), (SPX + SX * 7, SPY + SY * 11 - 2),
    (SPX + SX * 8, SPY + SY * 11 - 2), (SPX + SX * 9, SPY + SY * 11 - 2),  # 12
    # 13-2
    (SPX, SPY + SY * 12 - 2), (SPX + SX, SPY + SY * 12 - 2), (SPX + SX * 2, SPY + SY * 12 - 2),
    (SPX + SX * 3, SPY + SY * 12 - 2), (SPX + SX * 4, SPY + SY * 12 - 2),
    (SPX + SX * 5, SPY + SY * 12 - 2), (SPX + SX * 6, SPY + SY * 12 - 2), (SPX + SX * 7, SPY + SY * 12 - 2),
    (SPX + SX * 8, SPY + SY * 12 - 2), (SPX + SX * 9, SPY + SY * 12 - 2),  # 13
    # 14-2
    (SPX, SPY + SY * 13 - 2), (SPX + SX, SPY + SY * 13 - 2), (SPX + SX * 2, SPY + SY * 13 - 2),
    (SPX + SX * 3, SPY + SY * 13 - 2), (SPX + SX * 4, SPY + SY * 13 - 2),
    (SPX + SX * 5, SPY + SY * 13 - 2), (SPX + SX * 6, SPY + SY * 13 - 2), (SPX + SX * 7, SPY + SY * 13 - 2),
    (SPX + SX * 8, SPY + SY * 13 - 2), (SPX + SX * 9, SPY + SY * 13 - 2),  # 14
    # 15-2
    (SPX, SPY + SY * 14 - 2), (SPX + SX, SPY + SY * 14 - 2), (SPX + SX * 2, SPY + SY * 14 - 2),
    (SPX + SX * 3, SPY + SY * 14 - 2), (SPX + SX * 4, SPY + SY * 14 - 2),
    (SPX + SX * 5, SPY + SY * 14 - 2), (SPX + SX * 6, SPY + SY * 14 - 2), (SPX + SX * 7, SPY + SY * 14 - 2),
    (SPX + SX * 8, SPY + SY * 14 - 2), (SPX + SX * 9, SPY + SY * 14 - 2),  # 15
    # 16-3
    (SPX, SPY + SY * 15 - 3), (SPX + SX, SPY + SY * 15 - 3), (SPX + SX * 2, SPY + SY * 15 - 3),
    (SPX + SX * 3, SPY + SY * 15 - 3), (SPX + SX * 4, SPY + SY * 15 - 3),
    (SPX + SX * 5, SPY + SY * 15 - 3), (SPX + SX * 6, SPY + SY * 15 - 3), (SPX + SX * 7, SPY + SY * 15 - 3),
    (SPX + SX * 8, SPY + SY * 15 - 3), (SPX + SX * 9, SPY + SY * 15 - 3),  # 16
    # 17-3
    (SPX, SPY + SY * 16 - 3), (SPX + SX, SPY + SY * 16 - 3), (SPX + SX * 2, SPY + SY * 16 - 3),
    (SPX + SX * 3, SPY + SY * 16 - 3), (SPX + SX * 4, SPY + SY * 16 - 3),
    (SPX + SX * 5, SPY + SY * 16 - 3), (SPX + SX * 6, SPY + SY * 16 - 3), (SPX + SX * 7, SPY + SY * 16 - 3),
    (SPX + SX * 8, SPY + SY * 16 - 3), (SPX + SX * 9, SPY + SY * 16 - 3),  # 17
    # 18-3
    (SPX, SPY + SY * 17 - 3), (SPX + SX, SPY + SY * 17 - 3), (SPX + SX * 2, SPY + SY * 17 - 3),
    (SPX + SX * 3, SPY + SY * 17 - 3), (SPX + SX * 4, SPY + SY * 17 - 3),
    (SPX + SX * 5, SPY + SY * 17 - 3), (SPX + SX * 6, SPY + SY * 17 - 3), (SPX + SX * 7, SPY + SY * 17 - 3),
    (SPX + SX * 8, SPY + SY * 17 - 3), (SPX + SX * 9, SPY + SY * 17 - 3),  # 18
    # 19-3
    (SPX, SPY + SY * 18 - 3), (SPX + SX, SPY + SY * 18 - 3), (SPX + SX * 2, SPY + SY * 18 - 3),
    (SPX + SX * 3, SPY + SY * 18 - 3), (SPX + SX * 4, SPY + SY * 18 - 3),
    (SPX + SX * 5, SPY + SY * 18 - 3), (SPX + SX * 6, SPY + SY * 18 - 3), (SPX + SX * 7, SPY + SY * 18 - 3),
    (SPX + SX * 8, SPY + SY * 18 - 3), (SPX + SX * 9, SPY + SY * 18 - 3),  # 19
    # 20-4
    (SPX, SPY + SY * 19 - 3), (SPX + SX, SPY + SY * 19 - 3), (SPX + SX * 2, SPY + SY * 19 - 3),
    (SPX + SX * 3, SPY + SY * 19 - 3), (SPX + SX * 4, SPY + SY * 19 - 3),
    (SPX + SX * 5, SPY + SY * 19 - 3), (SPX + SX * 6, SPY + SY * 19 - 3), (SPX + SX * 7, SPY + SY * 19 - 3),
    (SPX + SX * 8, SPY + SY * 19 - 3), (SPX + SX * 9, SPY + SY * 19 - 3),  # 20
    # 21-4
    (SPX, SPY + SY * 20 - 3), (SPX + SX, SPY + SY * 20 - 3), (SPX + SX * 2, SPY + SY * 20 - 3),
    (SPX + SX * 3, SPY + SY * 20 - 3), (SPX + SX * 4, SPY + SY * 20 - 3),
    (SPX + SX * 5, SPY + SY * 20 - 3), (SPX + SX * 6, SPY + SY * 20 - 3), (SPX + SX * 7, SPY + SY * 20 - 3),
    (SPX + SX * 8, SPY + SY * 20 - 3), (SPX + SX * 9, SPY + SY * 20 - 3),  # 21
    # 22-5
    (SPX, SPY + SY * 21 - 3), (SPX + SX, SPY + SY * 21 - 3), (SPX + SX * 2, SPY + SY * 21 - 3),
    (SPX + SX * 3, SPY + SY * 21 - 3), (SPX + SX * 4, SPY + SY * 21 - 3),
    (SPX + SX * 5, SPY + SY * 21 - 3), (SPX + SX * 6, SPY + SY * 21 - 3), (SPX + SX * 7, SPY + SY * 21 - 3),
    (SPX + SX * 8, SPY + SY * 21 - 3), (SPX + SX * 9, SPY + SY * 21 - 3),  # 22
)


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def block(count_page):
    list_cod = []
    num_page = 1

    for y in range(count_page):
        for i in range(20):
            # TODO (ИСПОЛНЕНО) перенести временные jpg файлы в папку temp
            filename = os.getcwd() + '\\tmp\\order' + str(num_page) + '.jpg'
            img = ImagePIL.open(filename)
            img.load()
            crop_img = img.crop(QR_IN[i])
            # crop_img.save('crop_img.jpg')
            data = decode(crop_img)
            list_cod.append(data[0].data)
            # encoded = encode(data[0].data, scheme='', size='20x20')
            # img_encoded = ImagePIL.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            # img_encoded.save('img_encoded.jpg')
        num_page += 1

    return list_cod


def convert_pdf2img(input_file: str, pages: Tuple = None):
    """Преобразует PDF в изображение и создает файл за страницей"""
    # Open the document

    pdf_in = fitz.open(input_file)
    output_files = []
    i = 0
    count_page = 0
    # Полистаем страницы
    for page in pdf_in:
        i += 1
        if str(pages) != str(None):
            if str(page) not in str(pages):
                continue
        # Выберем страницу
        # rotate = int(0)
        # PDF Страница конвертируется в целое изображение 1056 * 816, а затем для каждого изображения делается снимок экрана.
        # zoom = 1.33333333 -----> Размер изображения = 1056 * 816
        # zoom = 2 ---> 2 * Разрешение по умолчанию (текст четкий, текст изображения плохо читается) = маленький размер файла/размер изображения = 1584 * 1224
        # zoom = 4 ---> 4 * Разрешение по умолчанию (текст четкий, текст изображения плохо читается) = большой размер файла
        # zoom = 8 ---> 8 * Разрешение по умолчанию (текст четкий, текст изображения читается) = большой размер файла
        zoom_x = 2.08
        zoom_y = 2.08
        # Коэффициент масштабирования равен 2, чтобы текст был четким
        # Pre-rotate - это вращение при необходимости.
        mat = fitz.Matrix(zoom_x, zoom_y)  # .preRotate(rotate)
        # pix = page.getPixmap(matrix=mat, alpha=False)
        output_file = os.getcwd() + "\\tmp\\order" + str(i) + ".jpg"
        pix = page.get_pixmap(matrix=mat)
        # pix.writePNG(output_file)
        pix.save(output_file)
        output_files.append(output_file)
        count_page = i
    pdf_in.close()
    # summary = {
    #    "Исходный файл": input_file, "Страниц": str(pages), "Выходной файл(ы)": str(output_files)
    # }
    # Printing Summary
    # print("#### Отчет ########################################################")
    # print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
    # print("###################################################################")
    return count_page


def convertPdfToJpg(name):
    count_page = convert_pdf2img(name)
    return block(count_page)

