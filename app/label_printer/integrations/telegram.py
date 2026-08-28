import logging
import time

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


def send_message(message):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(
            url,
            data={"chat_id": settings.TELEGRAM_CHAT_ID, "text": message, "parse_mode": "MarkDown"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        logger.error("Telegram message was not sent: %s", error)
        return False
    return True


def send_document(document_path, *, max_retries=3, backoff_seconds=5):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with document_path.open("rb") as document:
                response = requests.post(
                    url,
                    data={
                        "chat_id": settings.TELEGRAM_CHAT_ID,
                        "caption": f"📦 Резервная копия: {document_path.name}",
                    },
                    files={"document": document},
                    timeout=60,
                )
            response.raise_for_status()
            return
        except requests.RequestException as error:
            last_error = error
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
    raise last_error
