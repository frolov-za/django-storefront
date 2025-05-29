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
    
def get_zpl_diagnostics(printer):
    command = "~HS"  # статусный запрос

    if printer.connection_type == "usb":
        raw = _send_via_usb(command, printer, expect_response=True)
    else:
        try:
            with socket.create_connection((printer.address, printer.port), timeout=5) as sock:
                sock.settimeout(3)
                sock.sendall(command.encode())
                raw = sock.recv(8192).decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Ошибка диагностики принтера: {str(e)}")
            return {"error": f"Ошибка подключения: {str(e)}"}

    try:
        return parse_zebra_hs_response(raw)
    except Exception as e:
        logger.error(f"Ошибка парсинга ответа ~HS: {str(e)}")
        return {"raw": raw, "error": "Ошибка парсинга"}

def parse_zebra_hs_response(raw_response):
    lines = raw_response.replace('\x02', '').replace('\x03', '').strip().splitlines()

    result = {}

    if len(lines) >= 1:
        parts = lines[0].split(',')
        result['free_memory_kb'] = int(parts[0])
        result['paper_out'] = parts[1] == '1'
        result['printhead_overheat'] = parts[2] == '1'
        result['head_temp'] = int(parts[3])
        result['ribbon_out'] = parts[5] == '1'
        result['ready'] = parts[6] == '1'
        result['connected'] = parts[7] == '1'

    if len(lines) >= 3:
        result['total_labels_printed'] = int(lines[2].split(',')[0])

    return result

def parse_zpl_help_output(raw_text):
    lines = raw_text.strip().splitlines()
    parsed = []

    for line in lines:
        if line.startswith('! U1 getvar'):
            parts = line.split('"')
            if len(parts) >= 3:
                variable = parts[1]
                value = parts[2].strip()
                parsed.append({
                    'variable': variable,
                    'value': value,
                })
    return parsed