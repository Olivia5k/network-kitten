from logbook import more


def setup_color():
    color = more.ColorizedStderrHandler()
    color.push_application()
