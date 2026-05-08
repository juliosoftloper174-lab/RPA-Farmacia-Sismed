"""Logger module."""

from sys import stderr

from loguru import logger

from .paths import LOGS_DIR

_LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{extra} - <level>{message}</level>"
)
logger.remove()
logger.add(stderr, format=_LOGGER_FORMAT)
logger.add(
    str(LOGS_DIR) + "/{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="2 months",
    compression="zip",
    enqueue=True,
    backtrace=False,
    diagnose=True,
    format=_LOGGER_FORMAT,
)

__all__ = ("logger",)
