import logging
import socket


logger = logging.getLogger(__name__)


def send_zpl(zpl_data, printer):
    """Send a completed ZPL document through the printer's configured transport."""
    try:
        if printer.connection_type == "network":
            _send_via_network(zpl_data, printer)
        elif printer.connection_type == "usb":
            _send_via_usb(zpl_data, printer)
        else:
            raise ValueError(f"Unknown connection type: {printer.connection_type}")
    except (OSError, ValueError) as error:
        logger.error("Print failed for %s: %s", printer, error)
        return False
    return True


def _send_via_network(zpl_data, printer):
    with socket.create_connection((printer.address, printer.port), timeout=5) as sock:
        sock.sendall(zpl_data.encode())


def _send_via_usb(zpl_data, printer):
    with open(printer.device_path, "w") as device:
        device.write(zpl_data)
        device.flush()
