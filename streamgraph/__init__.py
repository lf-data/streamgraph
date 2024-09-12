from .base import Layer, Node, Chain, ConditionalNode, node
import logging
from colorama import init, Fore, Style
import builtins


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

class ColoredFormatter(logging.Formatter):
    FORMAT = "%(asctime)s - %(id)s - %(message)s"
    FORMAT_DEBUG = "%(asctime)s - %(message)s"

    FORMATS = {
        logging.DEBUG: LogColors.OKGRAY + FORMAT_DEBUG + LogColors.ENDC,
        logging.INFO: LogColors.OKCYAN + FORMAT + LogColors.ENDC,
        logging.WARNING: LogColors.WARNING + FORMAT + LogColors.ENDC,
        logging.ERROR: LogColors.FAIL + FORMAT + LogColors.ENDC,
        logging.CRITICAL: LogColors.BOLD + LogColors.FAIL + FORMAT + LogColors.ENDC
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configurazione del logger principale
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def print(*args, sep = " ", end = ""):
    # Concatena tutti gli argomenti in una singola stringa
    message = sep.join(map(str, args)) + end

    logger.debug(message)

builtins.print = print



__all__ = ['node', 'Layer', 'Node', "Chain", "ConditionalNode", "logger"]
