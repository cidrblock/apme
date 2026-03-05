import sys
import logging


_logger = None

log_level_map = {
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


def set_logger_channel(channel: str = ""):
    global _logger
    _logger = logging.getLogger(channel)
    handler = logging.StreamHandler(sys.stdout)
    # default formatter
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def set_log_level(level_str: str = "info"):
    global _logger
    level = log_level_map.get(level_str.lower(), None)
    _logger.setLevel(level)


def exception(*args, **kwargs):
    _logger.exception(*args, **kwargs)


def error(*args, **kwargs):
    _logger.error(*args, **kwargs)


def warning(*args, **kwargs):
    _logger.warning(*args, **kwargs)


def info(*args, **kwargs):
    _logger.info(*args, **kwargs)


def debug(*args, **kwargs):
    _logger.debug(*args, **kwargs)
