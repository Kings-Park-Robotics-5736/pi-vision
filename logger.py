import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

logger = logging.getLogger("ballfinder")
logger.setLevel(logging.DEBUG)

info = logger.info
debug = logger.debug
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

setLevel = logger.setLevel
