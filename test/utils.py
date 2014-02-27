import mock


def builtin(target):
    """
    Return the correct string to mock.patch depending on Py3k or not.

    """

    return '{0}.{1}'.format(
        'builtins' if mock.inPy3k else '__builtin__',
        target,
    )


def maybe_super(cls, self, key, *args, **kwargs):
    """
    Call a superclass method, but only if it actually exists.

    This avoids problems when doing multiple inherintance, and is mostly used
    with setup_method of the Mock classes above.

    """

    maybe = getattr(super(cls, self), key, None)
    if maybe:
        maybe(*args, **kwargs)
