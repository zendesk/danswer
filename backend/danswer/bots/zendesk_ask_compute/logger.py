import logging


def get_log_level_from_str(log_level_str: str) -> int:
    log_level_dict = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    return log_level_dict.get(log_level_str.upper(), logging.INFO)


def setup_logger(
    name: str = __name__,
    log_level_str: str = "info",
) -> logging.Logger:
    log_level = get_log_level_from_str(log_level_str)
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(log_level)

        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(filename)20s%(lineno)4s : %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

    return logger
