import socket
import logging

logger = logging.getLogger(__name__)

def send_zpl_to_printer(zpl_data, printer):
    try:
        if printer.connection_type == 'network':
            return _send_via_network(zpl_data, printer)
        elif printer.connection_type == 'usb':
            return _send_via_usb(zpl_data, printer)
        else:
            logger.error(f"Unknown connection type: {printer.connection_type}")
            return False
    except Exception as e:
        logger.error(f"Print error: {str(e)}")
        return False

def _send_via_network(zpl_data, printer):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((printer.address, printer.port))
            sock.sendall(zpl_data.encode())
            return True
    except Exception as e:
        logger.error(f"Network print error: {str(e)}")
        return False

def _send_via_usb(zpl_data, printer):
    try:
        with open(printer.device_path, 'w') as dev:
            dev.write(zpl_data)
            dev.flush()
        return True
    except PermissionError:
        logger.error(f"Permission denied for device: {printer.device_path}")
        return False
    except Exception as e:
        logger.error(f"USB print error: {str(e)}")
        return False