import logging


_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s"


def get_logger(name: str = "rookie3050", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
