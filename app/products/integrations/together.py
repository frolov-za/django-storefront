import requests
from django.conf import settings


class TogetherAPIError(Exception):
    """The Together API could not produce a usable completion."""


def generate_completion(prompt):
    if not settings.TOGETHER_API_KEY:
        raise TogetherAPIError("Не задан ключ Together API")

    try:
        response = requests.post(
            "https://api.together.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "prompt": prompt,
                "max_tokens": 600,
                "temperature": 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        raise TogetherAPIError("Не удалось получить ответ от Together API") from error

    content = _extract_content(data)
    if not content:
        raise TogetherAPIError("Together API вернул пустой ответ")
    return content


def _extract_content(data):
    """Support both the current chat response and the legacy response shape."""
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        pass
    try:
        return data["output"]["choices"][0]["text"].strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        return ""
