import socket


def port_open(ip, port):
    """
    Connect to a port to figure out if it is open or not.

    Mainly used by the main binary to check if the WolfServer is up or not.

    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False
