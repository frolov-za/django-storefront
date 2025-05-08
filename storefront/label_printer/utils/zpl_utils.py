from io import BytesIO
from zplgrf import GRF
from django.utils import timezone

def generate_zpl(config, product_name, barcode):
    zpl = [
        f"^XA",
        f"^PW{config.mm_to_dots(config.width_mm)}",
        f"^LL{config.mm_to_dots(config.height_mm)}",
        f"^FO{config.mm_to_dots(config.product_pos_x_mm)},{config.mm_to_dots(config.product_pos_y_mm)}",
        f"^FB{config.mm_to_dots(config.product_max_width_mm)},1,0,C,0",
        f"^FD{product_name}^FS",
        f"^FO{config.mm_to_dots(config.barcode_pos_x_mm)},{config.mm_to_dots(config.barcode_pos_y_mm)}",
        f"^BY2,,{config.mm_to_dots(config.barcode_height_mm)}",
        f"^B{config.barcode_type},N,N,N",
        f"^FD{barcode}^FS",
        f"^FO{config.mm_to_dots(config.date_pos_x_mm)},{config.mm_to_dots(config.date_pos_y_mm)}",
        f"^FB{config.mm_to_dots(20)},1,0,{config.date_rotation},0",
        f"^FD{timezone.now().strftime('%d %m %y %H-%M')}^FS",
        f"^XZ"
    ]
    return '\n'.join(zpl)

def generate_preview(config):
    try:
        zpl = generate_zpl(config, "Тестовый продукт", "123456789")
        grf = GRF.from_zpl(zpl)
        img_byte_arr = BytesIO()
        grf.to_image().save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"Ошибка: {str(e)}", fill=(255, 0, 0))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()