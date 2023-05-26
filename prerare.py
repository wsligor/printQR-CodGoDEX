import os
import fitz

from typing import Tuple
from PIL import Image as ImagePIL
from pylibdmtx.pylibdmtx import decode

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
            data = decode(crop_img)
            list_cod.append(data[0].data)
            # encoded = encode(data[0].data, scheme='', size='20x20')
            # img_encoded = ImagePIL.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
            # img_encoded.save('img_encoded.jpg')
        num_page += 1
        # TODO убрать заглушку для полной загрузки
        break
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
    return count_page

def convertPdfToJpg(name):
    # TODO Оптимизировать загрузку картинок из pdf файла
    # https: // dev - -gang - ru.turbopages.org / dev - gang.ru / s / article / rabota - s - pdf - failami - v - python - cztenie - i - razbor - 06 mta2spn0 /
    count_page = convert_pdf2img(name)
    return block(count_page)

