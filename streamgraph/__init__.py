"""This module initializes logging functionality.

Classes:
    - LogColors: A class defining color constants for logging
      messages using `colorama`.
    - ColoredJsonFormatter: A custom JSON log formatter that outputs
      colorized log records based on their severity level.

Functions:
    - add_fields(log_record, record, message_dict): Adds extra fields
      (e.g., timestamp, level, trace ID) to log records.
    - is_private_key(key): Checks if a log attribute is private
      (prefixed with "_").
    - set_extra_keys(record, log_record, reserved): Adds extra fields
      from log records, filtering out reserved and private attributes.
    - format(record): Formats log records and applies color
      based on log level.

Attributes:
    - __author__: Author information.
    - __email__: Contact email of the author.
    - __status__: Current status of the project (Development).
    - __version__: Module version (0.1.0).
    - DATE_FORMAT_TIMEZONE: A constant defining the
      datetime format used in logs.
    - logger: The logger object configured with a `ColoredJsonFormatter`
      to provide colorized JSON logs.

External Dependencies:
    - colorama: For terminal colorization.
    - python-json-logger: For logging in JSON format.

Usage:
    - The logger is initialized with a custom formatter that outputs JSON
      log records colorized by severity level.
    - `LogColors` provides convenient constants for applying colors
      to log messages in different contexts.
    - Chain components (`Layer`, `Node`, `Chain`) and conditional
      nodes (`IfNode`, `LoopNode`) are made available for
      use in higher-level modules.

Notes:
    - The logging system can be extended or replaced
      by other handlers as needed.
    - Use `__all__` to expose core chain components and
      utility functions for external use.
"""

import logging
import json
from uuid import uuid4
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger
from colorama import init, Fore, Style
from .components import Layer, Node, Chain, node
from .conditional_nodes import IfNode, LoopNode, ifnode, loopnode


__author__ = "Francesco Lorè"
__email__ = "flore9819@gmail.com"
__status__ = "Development"

__version__ = "0.1.0"

init(autoreset=True)


class LogColors:
    """
    A class that defines color constants for logging messages.

    This class provides a set of color constants using the
    `colorama` library, which can be used to colorize
    log messages in the terminal. The colors are defined using
    `colorama.Fore` and `colorama.Style` attributes.

    Attributes:
        OKCYAN (str): Color code for cyan text.
        OKGRAY (str): Color code for light black text (gray).
        WARNING (str): Color code for yellow text, typically used for warnings.
        FAIL (str): Color code for red text, typically used
                    for errors or failures.
        ENDC (str): Color code to reset the text color to the default.
        BOLD (str): Color code to set the text to bold.

    Notes:
        - `Fore` and `Style` are part of the `colorama` library and
        are used to apply colors and styles to terminal output.
        - The `ENDC` attribute is used to reset the text color back
        to the default after applying one of the color attributes.
    """

    OKCYAN = Fore.CYAN
    OKGRAY = Fore.LIGHTBLACK_EX
    WARNING = Fore.YELLOW
    FAIL = Fore.RED
    ENDC = Style.RESET_ALL
    BOLD = Style.BRIGHT


DATE_FORMAT_TIMEZONE = "%Y-%m-%dT%H:%M:%S.%fZ"


class ColoredJsonFormatter(jsonlogger.JsonFormatter):
    """A custom JSON formatter for logging with colorized output based.

    This formatter extends the `jsonlogger.JsonFormatter`
    to output log records in JSON format
    with colors applied based on the log level.
    The colors are defined in the `LogColors` class.

    Attributes:
        FORMATS (dict): A dictionary mapping logging levels
        to corresponding color codes.

    Methods:
        __init__(*args, **kwargs):
            Initializes the formatter and calls the superclass initializer.

        add_fields(log_record, record, message_dict):
            Adds extra fields to the log record, including timestamp,
            log level, and trace ID.

        is_private_key(key):
            Checks if the given key is a private attribute.

        set_extra_keys(record, log_record, reserved):
            Adds extra data from the log record to the final log output,
            filtering out reserved and private attributes.

        format(record):
            Formats the log record, applying color based on the log level.

    Args:
        *args: Variable length argument list passed
        to the parent `JsonFormatter` class.
        **kwargs: Keyword arguments passed to the parent `JsonFormatter` class.

    Notes:
        - The `FORMATS` attribute maps logging levels
        to colors defined in the `LogColors` class.
        - The `format` method is overridden to apply color formatting
        to the log message based on its severity.
        - The `add_fields` method enriches the log record with
        additional fields like timestamp and trace ID.
    """

    FORMATS = {
        logging.DEBUG: LogColors.OKGRAY,
        logging.INFO: LogColors.OKCYAN,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.FAIL,
        logging.CRITICAL: LogColors.BOLD + LogColors.FAIL,
    }

    def add_fields(self, log_record, record, message_dict):
        """Add additional fields to the log record.

        Args:
            log_record (dict): The dictionary of log record fields.
            record (logging.LogRecord): The log record instance.
            message_dict (dict): Dictionary of message parameters.
        """
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).strftime(
            DATE_FORMAT_TIMEZONE
        )
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
        """Determine if the given key is a private attribute.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key is a private attribute, False otherwise.
        """
        return hasattr(key, "startswith") and key.startswith("_")

    @staticmethod
    def set_extra_keys(record, log_record, reserved):
        """Add extra data to the log record, filtering out reserved attributes.

        Args:
            record (logging.LogRecord): The log record instance.
            log_record (dict): The dictionary of log record fields.
            reserved (list): List of reserved field names to be excluded.
        """
        record_items = list(record.__dict__.items())
        records_filtered_reserved = [
            item for item in record_items if item[0] not in reserved
        ]
        records_filtered_private_attr = [
            item
            for item in records_filtered_reserved
            if not ColoredJsonFormatter.is_private_key(item[0])
        ]

        for key, value in records_filtered_private_attr:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            log_record[key] = value

    def format(self, record):
        """Format the log record and applies color based on the log level.

        Args:
            record (logging.LogRecord): The log record instance.

        Returns:
            str: The formatted log message with color applied.
        """
        color = self.FORMATS.get(record.levelno, LogColors.ENDC)
        message = super().format(record)
        return f"{color}{message}{LogColors.ENDC}"


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredJsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


__all__ = [
    "node",
    "ifnode",
    "loopnode",
    "Layer",
    "Node",
    "Chain",
    "IfNode",
    "LoopNode",
    "logger",
]
