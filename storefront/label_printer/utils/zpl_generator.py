from datetime import datetime

def generate_zpl(product_name, barcode, template):
    width = 240  # 3cm * 80 dpi
    height = 160  # 2cm * 80 dpi
    date_str = datetime.now().strftime(template.date_format)
    
    # Штрихкод (центрирован)
    barcode_x = (width - 200) // 2
    barcode_y = 30
    barcode_code = f'^FO{barcode_x},{barcode_y}^BY2^BCN,{template.barcode_height},Y,N,N^FD{barcode}^FS'
    
    # Название товара (ниже штрихкода, центрировано)
    product_name_y = barcode_y + template.barcode_height + 10
    product_name_code = f'^FO0,{product_name_y}^FB{width},1,0,C,0^A0N,{template.product_name_font_size},{template.product_name_font_size}^FD{product_name}^FS'
    
    # Дата (справа, вертикально)
    date_x = width - 50
    date_code = f'^FO{date_x},30^A0R,{template.date_font_size},{template.date_font_size}^FD{date_str}^FS'
    
    return f"""
    ^XA
    ^LL{height}
    ^PW{width}
    {barcode_code}
    {product_name_code}
    {date_code}
    ^XZ
    """.strip()