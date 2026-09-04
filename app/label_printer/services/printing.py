import logging
from dataclasses import dataclass

from products.models import Product

from label_printer.integrations.printers.transport import send_zpl
from label_printer.integrations.printers.zpl import generate_zpl
from label_printer.models import LabelPrintLog, Printer


logger = logging.getLogger(__name__)


SUPPORTED_VOLUMES = {
    1000: "barcode",
    1500: "barcode15",
}


class PrintingError(Exception):
    """A user-facing error in the printing workflow."""


@dataclass(frozen=True)
class PrintResult:
    quantity: int = 1


def get_active_printer():
    """Select an explicitly active USB printer before a network printer."""

    logger.debug("Поиск активного принтера")

    printer = (
        Printer.objects
        .filter(is_active=True, connection_type="usb")
        .first()
        or Printer.objects
        .filter(is_active=True, connection_type="network")
        .first()
    )

    if not printer:
        logger.warning("Активный принтер не найден")
        raise PrintingError("Принтер не настроен")

    if not printer.label_template:
        logger.warning(
            "У активного принтера отсутствует шаблон этикетки: printer_id=%s",
            printer.id,
        )
        raise PrintingError("Принтер не настроен")

    logger.debug(
        "Активный принтер найден: printer_id=%s, "
        "connection_type=%s",
        printer.id,
        printer.connection_type,
    )

    return printer


def print_custom_labels(*, product_name, barcode, quantity) -> PrintResult:
    logger.debug(
        "Запрос на печать пользовательских этикеток: "
        "product_name=%r, barcode=%s, quantity=%s",
        product_name,
        barcode,
        quantity,
    )

    if not product_name:
        logger.warning(
            "Не указано наименование товара для пользовательской печати"
        )
        raise PrintingError("Не указано наименование товара")

    if barcode in (None, ""):
        logger.warning(
            "Не указан артикул для пользовательской печати"
        )
        raise PrintingError("Не указан артикул")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError) as error:
        logger.warning(
            "Некорректное количество этикеток: %r",
            quantity,
        )
        raise PrintingError("Количество должно быть числом") from error

    if quantity <= 0:
        logger.warning(
            "Указано некорректное количество этикеток: %s",
            quantity,
        )
        raise PrintingError("Количество должно быть больше 0")

    try:
        printer = get_active_printer()

        logger.debug(
            "Генерация ZPL для пользовательской печати: "
            "product_name=%r, printer_id=%s, quantity=%s",
            product_name,
            printer.id,
            quantity,
        )

        zpl_label = generate_zpl(
            product_name,
            str(barcode),
            printer.label_template,
        )

        logger.debug(
            "Отправка пользовательских этикеток на принтер: "
            "product_name=%r, printer_id=%s, quantity=%s",
            product_name,
            printer.id,
            quantity,
        )

        if not send_zpl(zpl_label * quantity, printer):
            logger.error(
                "Принтер не подтвердил печать пользовательских этикеток: "
                "product_name=%r, printer_id=%s, quantity=%s",
                product_name,
                printer.id,
                quantity,
            )
            raise PrintingError("Ошибка печати")

    except PrintingError:
        raise

    except Exception:
        logger.exception(
            "Непредвиденная ошибка при печати пользовательских этикеток: "
            "product_name=%r, quantity=%s",
            product_name,
            quantity,
        )
        raise

    logger.info(
        "Пользовательские этикетки успешно напечатаны: "
        "product_name=%r, количество=%s",
        product_name,
        quantity,
    )

    return PrintResult(quantity=quantity)


def transform_variable_measure_ean13(product_barcode, volume):
    """
    Формирует 12-значную основу EAN-13 для товара
    с переменной величиной (объёмом).

    Поддерживаются варианты артикула:
    - 7 цифр  — только код товара;
    - 12 цифр — код товара + базовый объём;
    - 13 цифр — EAN-13, последняя цифра является контрольной.

    Контрольная цифра не рассчитывается — её добавляет
    принтер при печати через ZPL.
    """

    logger.debug(
        "Формирование штрихкода EAN-13: barcode=%s, volume=%s",
        product_barcode,
        volume,
    )

    try:
        barcode = str(product_barcode).strip()
        volume = int(volume)
    except (TypeError, ValueError) as error:
        logger.warning(
            "Некорректный артикул или объём при формировании EAN-13: "
            "barcode=%r, volume=%r",
            product_barcode,
            volume,
        )
        raise PrintingError(
            "Некорректный артикул или объём"
        ) from error

    if not barcode.isdigit():
        logger.warning(
            "Артикул содержит недопустимые символы: barcode=%s",
            barcode,
        )
        raise PrintingError(
            "Артикул должен содержать только цифры"
        )

    if len(barcode) == 13:
        # Последняя цифра EAN-13 — контрольная.
        barcode = barcode[:-1]

    if len(barcode) == 7:
        # Артикул содержит только код товара.
        product_part = barcode

    elif len(barcode) == 12:
        # Последние 5 цифр — старый объём.
        product_part = barcode[:-5]

    else:
        logger.warning(
            "Недопустимая длина артикула для EAN-13: length=%s",
            len(barcode),
        )
        raise PrintingError(
            "Артикул должен содержать 7, 12 или 13 цифр"
        )

    if not 0 <= volume <= 99999:
        logger.warning(
            "Недопустимый объём для EAN-13: volume=%s",
            volume,
        )
        raise PrintingError(
            "Объём должен содержать не более 5 цифр"
        )

    # 100  -> 00100
    # 1000 -> 01000
    # 2500 -> 02500
    volume_code = f"{volume:05d}"

    result = f"{product_part}{volume_code}"

    if len(result) != 12:
        logger.error(
            "Не удалось сформировать 12-значную основу EAN-13: "
            "product_part=%s, volume=%s, result=%s",
            product_part,
            volume,
            result,
        )
        raise PrintingError(
            "Не удалось сформировать 12-значную основу EAN-13"
        )

    logger.debug(
        "Штрихкод EAN-13 успешно сформирован: volume=%s, barcode=%s",
        volume,
        result,
    )

    return result


def print_product_label(*, product_id, volume) -> PrintResult:
    logger.debug(
        "Запрос на печать этикетки товара: "
        "product_id=%s, volume=%s",
        product_id,
        volume,
    )

    try:
        volume = int(volume)
    except (TypeError, ValueError) as error:
        logger.warning(
            "Некорректный объём для печати: %r",
            volume,
        )
        raise PrintingError("Некорректный объём") from error

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist as error:
        logger.warning(
            "Продукт не найден: product_id=%s",
            product_id,
        )
        raise PrintingError("Продукт не найден") from error

    logger.debug(
        "Продукт найден: product_id=%s, name=%r, weight_product=%s",
        product.id,
        product.name,
        product.weight_product,
    )

    barcode = product.barcode

    if not barcode:
        logger.warning(
            "Для товара не задан артикул: "
            "product_id=%s, name=%r",
            product.id,
            product.name,
        )
        raise PrintingError("Для товара не задан артикул")

    if product.weight_product:
        logger.debug(
            "Печать весового товара: "
            "product_id=%s, name=%r, volume=%s, исходный barcode=%s",
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
            "product_id=%s, name=%r, volume=%s, barcode=%s",
            product.id,
            product.name,
            volume,
            barcode,
        )

    else:
        logger.debug(
            "Печать обычного товара: "
            "product_id=%s, name=%r, volume=%s, barcode=%s",
            product.id,
            product.name,
            volume,
            barcode,
        )

        try:
            barcode_field = SUPPORTED_VOLUMES[volume]
        except KeyError as error:
            logger.warning(
                "Неподдерживаемый объём для обычного товара: "
                "product_id=%s, name=%r, volume=%s",
                product.id,
                product.name,
                volume,
            )
            raise PrintingError(
                "Поддерживаются только объёмы 1 и 1,5 литра"
            ) from error

        barcode = getattr(product, barcode_field)

        if not barcode:
            logger.warning(
                "Для выбранного объёма не задан артикул: "
                "product_id=%s, name=%r, volume=%s, field=%s",
                product.id,
                product.name,
                volume,
                barcode_field,
            )
            raise PrintingError(
                "Для выбранного объёма не задан артикул"
            )

        logger.debug(
            "Использован barcode для тары: "
            "product_id=%s, name=%r, volume=%s, field=%s, barcode=%s",
            product.id,
            product.name,
            volume,
            barcode_field,
            barcode,
        )

    try:
        printer = get_active_printer()

        logger.debug(
            "Генерация ZPL: "
            "product_id=%s, name=%r, printer_id=%s",
            product.id,
            product.name,
            printer.id,
        )

        zpl_data = generate_zpl(
            product.name,
            barcode,
            printer.label_template,
        )

        logger.debug(
            "Отправка этикетки на принтер: "
            "product_id=%s, name=%r, printer_id=%s, volume=%s",
            product.id,
            product.name,
            printer.id,
            volume,
        )

        error = send_zpl(zpl_data, printer)

    except PrintingError:
        raise

    except Exception:
        logger.exception(
            "Непредвиденная ошибка при печати товара: "
            "product_id=%s, name=%r, volume=%s",
            product.id,
            product.name,
            volume,
        )
        raise

    if error is not True:
        logger.error(
            "Ошибка печати товара: "
            "product_id=%s, name=%r, volume=%s, barcode=%s, error=%s",
            product.id,
            product.name,
            volume,
            barcode,
            error,
        )

        raise PrintingError(f"Ошибка печати: {error}")

    try:
        LabelPrintLog.objects.create(
            product_name=product.name,
            barcode=barcode,
            volume=volume,
        )
    except Exception:
        logger.exception(
            "Этикетка напечатана, но не удалось записать "
            "результат в журнал печати: "
            "product_id=%s, name=%r, volume=%s",
            product.id,
            product.name,
            volume,
        )

    logger.info(
        "Этикетка успешно напечатана: "
        "product_id=%s, name=%r, volume=%s",
        product.id,
        product.name,
        volume,
    )

    return PrintResult()