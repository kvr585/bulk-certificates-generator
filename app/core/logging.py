import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """Configure standard application logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Silence overly verbose third-party loggers if not in debug
    if not debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("bulk_certificate_generator")
