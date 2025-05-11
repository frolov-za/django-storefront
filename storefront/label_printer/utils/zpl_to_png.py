import requests

def zpl_to_png(zpl: str) -> bytes:
    try:
        response = requests.post(
            'http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/',
            headers={'Accept': 'image/png'},
            data=zpl.encode('utf-8'),
            timeout=5  # безопасный таймаут
        )
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        print(f"Labelary вернул ошибку {response.status_code}: {response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при соединении с Labelary: {e}")
        raise

# def zpl_to_png(zpl: str) -> bytes:
#     url = "http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/"

#     headers = {'Accept': 'image/png'}
#     response = requests.post(url, headers=headers, data=zpl.encode('utf-8'))

#     # Если ошибка — выбросить исключение с объяснением
#     if not response.ok:
#         raise RuntimeError(
#         f'Labelary API error {response.status_code}: {response.text}'
#     )

#     return response.content