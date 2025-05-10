from datetime import datetime
import pytz

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
    product_name_y = barcode_y + template.barcode_height + 10
    product_name_code = f'^FO{template.product_position}^FB230,7,0,C^A{template.font_letter}N,{template.product_name_font_size},{template.product_name_font_size}^FD{product_name}^FS'
    
    # Дата (справа, вертикально)
    #date_x = width - 50
    date_code = f'^FO{template.date_position}^FB100,7,0,C^A0B,{template.date_font_size},{template.date_font_size}^FD{date_str}^FS'
    
    return f"""
    ^XA
    ^LL{height}
    ^PW{width}
    {barcode_code}
    {font}
    {product_name_code}
    {date_code}
    ^XZ
    """.strip()