import logging
import os


def setup_logger():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("logs/protrack.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


setup_logger()
