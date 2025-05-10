import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from barcode import EAN13
from barcode.writer import ImageWriter
from datetime import datetime

def generate_label(barcode, product_name, expiry_date):
    # Параметры изображения (3x2 см при 203 DPI)
    width_px = 240
    height_px = 160
    
    main_image = Image.new('L', (width_px, height_px), 255)
    draw = ImageDraw.Draw(main_image)

    # Генерация штрих-кода
    try:
        buff = BytesIO()
        options = {
            'module_width': 0.17,
            'module_height': 7.0,
            'quiet_zone': 1.0,
            'text_distance': 2,
            'font_size': 4,
        }
        EAN13(str(barcode), writer=ImageWriter()).write(buff, options=options)
        buff.seek(0)
        barcode_img = Image.open(buff)
        main_image.paste(barcode_img, (0, 5))  # Смещение на 5px сверху
    except Exception as e:
        raise ValueError(f"Barcode error: {e}")

    # Загрузка шрифтов
    try:
        font_bold = ImageFont.truetype("arial.ttf", 264)
        font_regular = ImageFont.truetype("arial.ttf", 17)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Блок текста слева
    y_position = barcode_img.height + 1
    
    # Название продукта
    draw.text((15, y_position-10), product_name, font=font_regular, align= "center",  fill=0)
    
    # Блок справа (вертикальный текст)
    date_block = Image.new('L', (90, 170), 255)
    date_draw = ImageDraw.Draw(date_block)
    
    # Форматирование даты
    expiry_str = expiry_date.strftime("%d/%m/%y")
    time_str = expiry_date.strftime("%H:%M")
    date_text = f"{expiry_str} {time_str}"
    
    date_draw.text((0, 0), date_text, font=font_small, align= "center", fill=0)
    rotated_date = date_block.rotate(90, expand=True)
#    main_image.paste(rotated_date, (width_px - rotated_date.width - 5, 40))

    # Конвертация в ZPL
    main_image = ImageOps.invert(main_image.convert('1'))
    bytes_per_row = (main_image.width + 7) // 8
    total_bytes = bytes_per_row * main_image.height
    hex_data = main_image.tobytes().hex().upper()

    return f"""^XA
^FO0,0
^GFA,{total_bytes},{total_bytes},{bytes_per_row},{hex_data}
^FS
^XZ
"""

# Пример использования
if __name__ == "__main__":
    zpl_code = generate_label(
        barcode="521397107586",
        product_name="Blue Moon Beer Разливное",
        expiry_date=datetime(2025, 5, 10, 14, 35, 22)
    )
    print(zpl_code)