from datetime import datetime
from pathlib import Path

import pytz
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps


MOSCOW_TZ = pytz.timezone("Europe/Moscow")


def generate_zpl(product_name, barcode, template):
    """Render one label into ZPL using the selected label template."""
    width = int(template.label_wight)
    height = int(template.label_hight)
    date_str = datetime.now(MOSCOW_TZ).strftime(template.date_format)

    font = f"^CW{template.font_letter},{template.font_name}^CI28^FS"
    barcode_code = (
        f"^FO{template.barcode_position}^BEN,{template.barcode_height},Y,N,{template.barcode_control_digit}"
        f"^FD{barcode}^FS"
    )
    product_name_code = (
        f"^FO{template.product_position}^FB230,7,0,C"
        f"^A{template.font_letter}N,{template.product_name_font_size},"
        f"{template.product_name_font_size}^FD{product_name}^FS"
    )

    product_image = Image.new("L", (width, 20), 255)
    draw = ImageDraw.Draw(product_image)
    font_path = Path(settings.BASE_DIR) / "static/font/times_new_roman.ttf"
    try:
        pillow_font = ImageFont.truetype(font_path, 20)
    except OSError:
        pillow_font = ImageFont.load_default()
    draw.text((0, 0), product_name, font=pillow_font, align="center", fill=0)

    product_image = ImageOps.invert(product_image.convert("1"))
    bytes_per_row = (product_image.width + 7) // 8
    total_bytes = bytes_per_row * product_image.height
    hex_data = product_image.tobytes().hex().upper()
    product_image_code = (
        f"^FO{template.product_position}^GFA,{total_bytes},{total_bytes},"
        f"{bytes_per_row},{hex_data}^FS"
    )
    date_code = (
        f"^FO{template.date_position}^FB100,7,0,C"
        f"^A0B,{template.date_font_size},{template.date_font_size}^FD{date_str}^FS"
    )

    return "\n".join(
        line
        for line in (
            "^XA",
            f"^LL{height}",
            f"^PW{width}",
            barcode_code,
            "" if template.product_name_via_pillow else font,
            product_image_code if template.product_name_via_pillow else product_name_code,
            date_code,
            "^XZ",
        )
        if line.strip()
    )
