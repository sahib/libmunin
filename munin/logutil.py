#!/usr/bin/env python
# encoding: utf-8


import logging
import logging.handlers

###########################################################################
#          Code taken from moosecat (shameless self-plagiatism)           #
###########################################################################

# Loggin related
COLORED_FORMAT = "%(asctime)s%(reset)s %(log_color)s{logsymbol} \
%(levelname)-8s%(reset)s %(bold_blue)s[%(filename)s:%(lineno)3d]%(reset)s \
%(bold_black)s%(name)s:%(reset)s %(message)s"

SIMPLE_FORMAT = "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)3d] \
%(name)s: %(message)s"

DATE_FORMAT = "%H:%M:%S"
UNICODE_ICONS = {
    logging.DEBUG: '⚙',
    logging.INFO: '⚐',
    logging.WARNING: '⚠',
    logging.ERROR: '⚡',
    logging.CRITICAL: '☠'
}


def create_logger(name=None, log_file=None, verbosity=logging.DEBUG):
    '''Create a new Logger configured with moosecat's defaults.

    :name: A user-define name that describes the logger
    :return: A new logger .
    '''
    logger = logging.getLogger(name)

    # This is hack to see if this function was already called
    if len(logging.getLogger(None).handlers) is 2:
        return logger

    # Defaultformatter, used for File logging,
    # and for stdout if colorlog is not available
    formatter = logging.Formatter(
        SIMPLE_FORMAT,
        datefmt=DATE_FORMAT
    )

    # Try to load the colored log and use it on success.
    # Else we'll use the SIMPLE_FORMAT
    try:
        import colorlog

        class SymbolFormatter(colorlog.ColoredFormatter):
            def format(self, record):
                result = colorlog.ColoredFormatter.format(self, record)
                return result.format(logsymbol=UNICODE_ICONS[record.levelno])
    except ImportError:
        # Take the normal one instead.
        col_formatter = formatter
    else:
        col_formatter = SymbolFormatter(
            COLORED_FORMAT,
            datefmt=DATE_FORMAT,
            reset=False
        )

    # Stdout-Handler
    stream = logging.StreamHandler()
    stream.setFormatter(col_formatter)

    if log_file is not None:
        # Rotating File-Handler
        file_stream = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=(1024 ** 2 * 10),  # 10 MB
            backupCount=2,
            delay=True
        )
        file_stream.setFormatter(formatter)
        logger.addHandler(file_stream)

    logger.addHandler(stream)
    logger.setLevel(verbosity)
    return logger


if __name__ == '__main__':
    logger = create_logger('Herbert', log_file='/tmp/munin.log')
    logger.debug('Hello, Im Herbert.')
    logger.info('I will be your logging guide for today.')
    logger.warning('You only need to call create_logger(None) for the root logger.')
    logger.error('Afterwards you can use logging.getLogger("module") to get loggers like me!')
    logger.critical("That's freaking cool, eh?")
