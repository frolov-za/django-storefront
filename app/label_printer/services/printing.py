from dataclasses import dataclass

from products.models import Product

from label_printer.integrations.printers.transport import send_zpl
from label_printer.integrations.printers.zpl import generate_zpl
from label_printer.models import LabelPrintLog, Printer
import logging

logger = logging.getLogger(__name__)

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



def transform_variable_measure_ean13(product_barcode, volume):
    """
    Формирует 12-значную основу EAN-13 для товара
    с переменной величиной (объёмом).

    Последняя цифра 13-значного EAN-13 считается контрольной
    и удаляется. Последние 5 цифр оставшейся 12-значной основы
    заменяются на новый объём.

    Контрольная цифра заново не рассчитывается — её добавляет
    принтер при печати через ZPL.
    """

    try:
        barcode = str(product_barcode).strip()
        volume = int(volume)
    except (TypeError, ValueError) as error:
        raise PrintingError(
            "Некорректный артикул или объём"
        ) from error

    if not barcode.isdigit():
        raise PrintingError(
            "Артикул должен содержать только цифры"
        )

    # Если передан полный EAN-13, удаляем контрольную цифру.
    if len(barcode) == 13:
        barcode = barcode[:-1]

    if len(barcode) != 12:
        raise PrintingError(
            "Артикул должен содержать 12 или 13 цифр"
        )

    if not 0 <= volume <= 99999:
        raise PrintingError(
            "Объём должен содержать не более 5 цифр"
        )

    # Первые цифры — код товара.
    # Последние 5 цифр — переменная величина.
    product_part = barcode[:-5]

    # 100   -> 00100
    # 1000  -> 01000
    # 2500  -> 02500
    volume_code = f"{volume:05d}"

    result = f"{product_part}{volume_code}"

    if len(result) != 12:
        raise PrintingError(
            "Не удалось сформировать 12-значную основу EAN-13"
        )

    return result


def print_product_label(*, product_id, volume) -> PrintResult:
    try:
        volume = int(volume)
    except (TypeError, ValueError) as error:
        raise PrintingError("Некорректный объём") from error

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist as error:
        raise PrintingError("Продукт не найден") from error

    barcode = product.barcode

    if not barcode:
        raise PrintingError("Для товара не задан артикул")

    if product.weight_product:
        logger.debug(
            "Печать весового товара: product_id=%s, name=%r, "
            "volume=%s, исходный barcode=%s",
            product.id,
            product.name,
            volume,
            barcode,
        )

        barcode = transform_variable_measure_ean13(
            barcode,
            volume,
        )

        logger.debug(
            "Сформирован штрихкод для весового товара: "
            "product_id=%s, volume=%s, barcode=%s",
            product.id,
            volume,
            barcode,
        )

    else:
        logger.debug(
            "Печать обычного товара: product_id=%s, name=%r, "
            "volume=%s, barcode=%s",
            product.id,
            product.name,
            volume,
            barcode,
        )

        try:
            barcode_field = SUPPORTED_VOLUMES[volume]
        except KeyError as error:
            raise PrintingError(
                "Поддерживаются только объёмы 1 и 1,5 литра"
            ) from error

        barcode = getattr(product, barcode_field)

        if not barcode:
            raise PrintingError(
                "Для выбранного объёма не задан артикул"
            )

        logger.debug(
            "Использован обычный barcode для тары: "
            "product_id=%s, volume=%s, field=%s, barcode=%s",
            product.id,
            volume,
            barcode_field,
            barcode,
        )

    printer = get_active_printer()

    zpl_data = generate_zpl(
        product.name,
        barcode,
        printer.label_template,
    )

    error = send_zpl(zpl_data, printer)

    if error is not True:
        logger.error(
            "Ошибка печати: product_id=%s, name=%r, "
            "volume=%s, barcode=%s, error=%s",
            product.id,
            product.name,
            volume,
            barcode,
            error,
        )

        raise PrintingError(f"Ошибка печати: {error}")

    LabelPrintLog.objects.create(
        product_name=product.name,
        barcode=barcode,
        volume=volume,
    )

    logger.debug(
        "Этикетка успешно отправлена: product_id=%s, name=%r, "
        "volume=%s, barcode=%s, weight_product=%s",
        product.id,
        product.name,
        volume,
        barcode,
        product.weight_product,
    )

    return PrintResult()