from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont, ImageOps

tz = pytz.timezone("Europe/Moscow") 

def generate_zpl(product_name, barcode, template):
    width = int(template.label_wight) if template.label_wight is not None else str("") # 3cm * 80 dpi
    height = int(template.label_hight) if template.label_hight is not None else str("")  # 2cm * 80 dpi
    date_str = datetime.now(tz).strftime(template.date_format)
    
    # Установка шрифта
    font = f'^CW{template.font_letter},{template.font_name}^CI28^FS'
    

    # Штрихкод (центрирован)
    #barcode_x = (width - 200) // 2
    barcode_y = 30
    barcode_code = f'^FO{template.barcode_position}^BEN,{template.barcode_height},Y,N,N^FD{barcode}^FS'
    
    # Название товара (ниже штрихкода, центрировано)
    # product_name_y = barcode_y + template.barcode_height + 10
    product_name_code = f'^FO{template.product_position}^FB230,7,0,C^A{template.font_letter}N,{template.product_name_font_size},{template.product_name_font_size}^FD{product_name}^FS'
    

    main_image = Image.new('L', (width, 20), 255)
    draw = ImageDraw.Draw(main_image)
    
    try:
        font_bold = ImageFont.truetype("./static/arial_bold.ttf", 20)
        font_regular = ImageFont.truetype("./static/times_new_roman.ttf", 20)
    except IOError:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()

    draw.text((0, 0), product_name, font=font_regular, align= "center",  fill=0)
    
    # Конвертация в ZPL
    main_image = ImageOps.invert(main_image.convert('1'))
    bytes_per_row = (main_image.width + 7) // 8
    total_bytes = bytes_per_row * main_image.height
    hex_data = main_image.tobytes().hex().upper()

    product_name_code_pil = f"""^FO{template.product_position}^GFA,{total_bytes},{total_bytes},{bytes_per_row},{hex_data}^FS"""

    # Дата (справа, вертикально)
    #date_x = width - 50
    date_code = f'^FO{template.date_position}^FB100,7,0,C^A0B,{template.date_font_size},{template.date_font_size}^FD{date_str}^FS'
    
    return f"""
    ^XA
    ^LL{height}
    ^PW{width}
    {barcode_code}
    {"" if template.product_name_via_pillow else font}
    {product_name_code_pil if template.product_name_via_pillow else product_name_code}
    {date_code}
    ^XZ
    """.strip()