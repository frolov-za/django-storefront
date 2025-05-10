import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime

def generate_label(product_name):
    # Параметры изображения (3x2 см при 203 DPI)
    width_px = 240
    height_px = 20
    
    main_image = Image.new('L', (width_px, height_px), 255)
    draw = ImageDraw.Draw(main_image)

    try:
        font_bold = ImageFont.truetype("times_new_roman.ttf", 20)
        font_regular = ImageFont.truetype("times_new_roman.ttf", 20)
    except IOError:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()

    draw.text((0, 0), product_name, font=font_bold, align= "center",  fill=0)
    
    # Конвертация в ZPL
    main_image = ImageOps.invert(main_image.convert('1'))
    bytes_per_row = (main_image.width + 7) // 8
    total_bytes = bytes_per_row * main_image.height
    hex_data = main_image.tobytes().hex().upper()

    return f"""
^GFA,{total_bytes},{total_bytes},{bytes_per_row},{hex_data}^FS
"""

# Пример использования
if __name__ == "__main__":
    zpl_code = generate_label(
        # barcode="521397107586",
        product_name="Blue Пиво Blue Пиво Blue Moon",
        # expiry_date=datetime(2025, 5, 10, 14, 35, 22)
    )
    print(zpl_code)