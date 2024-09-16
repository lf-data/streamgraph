from .base import Layer, Node, Chain, ConditionalNode, node
import logging
from colorama import init, Fore, Style
import json
from pythonjsonlogger import jsonlogger
from uuid import uuid4
from datetime import datetime, timezone


__author__ = 'Francesco Lorè'
__email__ = 'flore9819@gmail.com'
__status__ = 'Development'

__version__ = "0.1.0"

# Inizializza colorama
init(autoreset=True)

class LogColors:
    OKCYAN = Fore.CYAN
    OKGRAY = Fore.LIGHTBLACK_EX
    WARNING = Fore.YELLOW
    FAIL = Fore.RED
    ENDC = Style.RESET_ALL
    BOLD = Style.BRIGHT

DATE_FORMAT_TIMEZONE = "%Y-%m-%dT%H:%M:%S.%fZ"

class ColoredJsonFormatter(jsonlogger.JsonFormatter):
    FORMATS = {
        logging.DEBUG: LogColors.OKGRAY,
        logging.INFO: LogColors.OKCYAN,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.FAIL,
        logging.CRITICAL: LogColors.BOLD + LogColors.FAIL
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Update the timestamp format
        log_record["timestamp"] = datetime.now(timezone.utc).strftime(DATE_FORMAT_TIMEZONE)
        log_record["level"] = record.levelname
        log_record["type"] = "log"
        log_record["level_num"] = record.levelno
        log_record["logger_name"] = record.name
        trace = str(uuid4())

        if trace:
            log_record["trace_id"] = trace

        self.set_extra_keys(record, log_record, self._skip_fields)

    @staticmethod
    def is_private_key(key):
        return hasattr(key, "startswith") and key.startswith("_")

    @staticmethod
    def set_extra_keys(record, log_record, reserved):
        """
        Add the extra data to the log record.
        Prefix will be added to all custom tags.
        """
        record_items = list(record.__dict__.items())
        records_filtered_reserved = [item for item in record_items if item[0] not in reserved]
        records_filtered_private_attr = [item for item in records_filtered_reserved if
                                         not ColoredJsonFormatter.is_private_key(item[0])]

        for key, value in records_filtered_private_attr:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            log_record[key] = value

    def format(self, record):
        # Colorize the log message
        color = self.FORMATS.get(record.levelno, LogColors.ENDC)
        message = super().format(record)
        return f"{color}{message}{LogColors.ENDC}"


# Configurazione del logger principale
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredJsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)



__all__ = ['node', 'Layer', 'Node', "Chain", "ConditionalNode", "logger"]
