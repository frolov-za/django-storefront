import requests


def zpl_to_png(zpl: str) -> bytes:
    response = requests.post(
        "http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/",
        headers={"Accept": "image/png"},
        data=zpl.encode("utf-8"),
        timeout=5,
    )
    response.raise_for_status()
    return response.content
