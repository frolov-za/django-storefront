import socket

def send_zpl_to_printer(zpl_data, printer):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((printer.address, printer.port))
            sock.sendall(zpl_data.encode())
        return True
    except Exception as e:
        print(f"Error sending to printer: {e}")
        return False