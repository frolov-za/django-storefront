import logging
import time

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def send_message(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    logger.debug(
        "Отправка сообщения в Telegram: длина сообщения=%s",
        len(message),
    )

    try:
        response = requests.post(
            url,
            data={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "MarkDown",
            },
            timeout=5,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        logger.error(
            "Не удалось отправить сообщение в Telegram: %s",
            error,
        )
        return False

    logger.info("Сообщение успешно отправлено в Telegram")

    return True


def send_document(
    document_path,
    *,
    max_retries=3,
    backoff_seconds=5,
):
    url = (
        f"https://api.telegram.org/"
        f"bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    )

    last_error = None

    logger.debug(
        "Отправка документа в Telegram: файл=%s, "
        "максимальное количество попыток=%s",
        document_path,
        max_retries,
    )

    for attempt in range(1, max_retries + 1):
        logger.debug(
            "Попытка отправки документа в Telegram: %s/%s, файл=%s",
            attempt,
            max_retries,
            document_path.name,
        )

        try:
            with document_path.open("rb") as document:
                response = requests.post(
                    url,
                    data={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "caption": (
                            f"📦 Резервная копия: "
                            f"{document_path.name}"
                        ),
                    },
                    files={
                        "document": document,
                    },
                    timeout=60,
                )

            response.raise_for_status()

            logger.info(
                "Документ успешно отправлен в Telegram: файл=%s, попытка=%s",
                document_path.name,
                attempt,
            )

            return

        except requests.RequestException as error:
            last_error = error

            if attempt < max_retries:
                logger.warning(
                    "Не удалось отправить документ в Telegram: "
                    "файл=%s, попытка=%s/%s, ошибка=%s. "
                    "Повторная попытка через %s сек.",
                    document_path.name,
                    attempt,
                    max_retries,
                    error,
                    backoff_seconds * attempt,
                )

                time.sleep(backoff_seconds * attempt)

            else:
                logger.error(
                    "Не удалось отправить документ в Telegram "
                    "после %s попыток: файл=%s, ошибка=%s",
                    max_retries,
                    document_path.name,
                    error,
                )

    raise last_error