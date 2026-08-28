import logging
import socket


logger = logging.getLogger(__name__)


def get_diagnostics(printer):
    """Return Zebra ~HS diagnostics for a network printer.

    USB printer device files are write-only in the supported deployment, so a
    reliable status response cannot be requested from them.
    """
    if printer.connection_type == "usb":
        return {"error": "Диагностика USB-принтера не поддерживается."}

    try:
        with socket.create_connection((printer.address, printer.port), timeout=5) as sock:
            sock.settimeout(3)
            sock.sendall(b"~HS")
            raw = sock.recv(8192).decode("utf-8", errors="ignore")
    except OSError as error:
        logger.error("Printer diagnostics failed for %s: %s", printer, error)
        return {"error": f"Ошибка подключения: {error}"}

    try:
        return parse_zebra_hs_response(raw)
    except (IndexError, ValueError) as error:
        logger.error("Unable to parse ~HS response: %s", error)
        return {"raw": raw, "error": "Ошибка разбора ответа принтера"}


def parse_zebra_hs_response(raw_response):
    lines = raw_response.replace("\x02", "").replace("\x03", "").strip().splitlines()
    result = {}
    if lines:
        parts = lines[0].split(",")
        result.update(
            free_memory_kb=int(parts[0]),
            paper_out=parts[1] == "1",
            printhead_overheat=parts[2] == "1",
            head_temp=int(parts[3]),
            ribbon_out=parts[5] == "1",
            ready=parts[6] == "1",
            connected=parts[7] == "1",
        )
    if len(lines) >= 3:
        result["total_labels_printed"] = int(lines[2].split(",")[0])
    return result


def parse_zpl_help_output(raw_text):
    return [
        {"variable": parts[1], "value": parts[2].strip()}
        for line in raw_text.strip().splitlines()
        if line.startswith("! U1 getvar")
        for parts in [line.split('"')]
        if len(parts) >= 3
    ]
