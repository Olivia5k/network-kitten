class TerminalUI(object):
    def success(self, message):
        print('S: {0}'.format(message))

    def error(self, message):
        print('E: {0}'.format(message))
