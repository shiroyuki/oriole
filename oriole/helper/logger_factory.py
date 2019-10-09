import logging
import os
import typing


class LoggerFactory:
    __known_logger__ = dict()
    __logging_options__ = str(os.getenv('LOG_OPTS') or '').lower().split(' ')

    @staticmethod
    def get(name: str, level: typing.Optional[int] = None):
        if name in LoggerFactory.__known_logger__:
            return LoggerFactory.__known_logger__.get(name)

        level = level or getattr(logging, (os.getenv('LOG_LEVEL') or 'INFO').upper())
        minimalistic_mode = 'minimal' in LoggerFactory.__logging_options__

        formatter = logging.Formatter(
            '%(name)s: %(message)s'
            if minimalistic_mode
            else '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)

        logger = logging.Logger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

        LoggerFactory.__known_logger__[name] = logger

        return logger