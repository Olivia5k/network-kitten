from wolf.util import port_open

PORT = 5555


def main():
    if not port_open('localhost', PORT):
        print('Error: Server not running. Please start it with "wolf server".')
