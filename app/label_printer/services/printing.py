from dataclasses import dataclass

from products.models import Product

from label_printer.integrations.printers.transport import send_zpl
from label_printer.integrations.printers.zpl import generate_zpl
from label_printer.models import LabelPrintLog, Printer


SUPPORTED_VOLUMES = {1000: "barcode", 1500: "barcode15"}


class PrintingError(Exception):
    """A user-facing error in the printing workflow."""


@dataclass(frozen=True)
class PrintResult:
    quantity: int = 1


def get_active_printer():
    """Select an explicitly active USB printer before a network printer."""
    printer = (
        Printer.objects.filter(is_active=True, connection_type="usb").first()
        or Printer.objects.filter(is_active=True, connection_type="network").first()
    )
    if not printer or not printer.label_template:
        raise PrintingError("Принтер не настроен")
    return printer


def print_product_label(*, product_id, volume) -> PrintResult:
    try:
        volume = int(volume)
        barcode_field = SUPPORTED_VOLUMES[volume]
    except (KeyError, TypeError, ValueError) as error:
        raise PrintingError("Поддерживаются только объёмы 1 и 1,5 литра") from error

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist as error:
        raise PrintingError("Продукт не найден") from error

    barcode = getattr(product, barcode_field)
    if not barcode:
        raise PrintingError("Для выбранного объёма не задан артикул")

    printer = get_active_printer()
    zpl_data = generate_zpl(product.name, barcode, printer.label_template)
    if not send_zpl(zpl_data, printer):
        raise PrintingError("Ошибка печати")

    LabelPrintLog.objects.create(product_name=product.name, barcode=barcode, volume=volume)
    return PrintResult()


def print_custom_labels(*, product_name, barcode, quantity) -> PrintResult:
    if not product_name:
        raise PrintingError("Не указано наименование товара")
    if barcode in (None, ""):
        raise PrintingError("Не указан артикул")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError) as error:
        raise PrintingError("Количество должно быть числом") from error
    if quantity <= 0:
        raise PrintingError("Количество должно быть больше 0")

    printer = get_active_printer()
    zpl_label = generate_zpl(product_name, str(barcode), printer.label_template)
    if not send_zpl(zpl_label * quantity, printer):
        raise PrintingError("Ошибка печати")
    return PrintResult(quantity=quantity)
