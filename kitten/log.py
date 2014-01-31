from logbook import more


def setup_color():  # pragma: nocover
    color = more.ColorizedStderrHandler()
    color.format_string = '{0} {1}'.format(
        '[{record.time:%Y-%m-%d %H:%M:%S.%f}]',
        '{record.level_name}: {record.channel}: {record.message}',
    )
    color.push_application()
