from mock import inPy3k


def builtin(target):
    """
    Return the correct string to mock.patch depending on Py3k or not.

    """

    return '{0}.{1}'.format('builtins' if inPy3k else '__builtin__', target)
