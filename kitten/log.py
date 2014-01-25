from logbook import more


def setup_color():  # pragma: nocover
    color = more.ColorizedStderrHandler()
    color.push_application()
