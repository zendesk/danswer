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
    name: str = __name__, log_level_str: str = "info", 
) -> logging.LoggerAdapter:
    log_level = get_log_level_from_str(log_level_str)
    logger = logging.getLogger(name)

    logger.setLevel(log_level)

    return logger
