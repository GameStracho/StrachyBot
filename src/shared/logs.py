import inspect
import logging
from collections.abc import Mapping
from types import FrameType
from typing import Any, override
from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom Formatter to add colorama styling to python logging output."""

    # Map log levels to colorama styles
    LEVEL_COLORS: dict[int, str] = {
        logging.DEBUG: Fore.BLACK + Style.BRIGHT,
        logging.INFO: Fore.GREEN + Style.BRIGHT,
        logging.WARNING: Fore.YELLOW + Style.BRIGHT,
        logging.ERROR: Fore.RED + Style.BRIGHT,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    @override
    def format(self, record: logging.LogRecord) -> str:
        # Get color for current log level (default to reset)
        level_color: str = self.LEVEL_COLORS.get(record.levelno, Style.RESET_ALL)

        # Style individual components
        timestamp: str = f"{Fore.BLACK}{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}"
        module_name: str = f"{Fore.BLACK}[{record.name}]{Style.RESET_ALL}"
        
        # Right-pad category for clean alignment
        level_tag:str = f"{level_color}{record.levelname:<8}{Style.RESET_ALL}"

        message: str = record.getMessage()

        return f"{timestamp} {module_name} {level_tag} {message}"


class ModuleLogger(logging.Logger):
    """Custom Logger that dynamically replaces record.name with the caller's module name."""

    @override
    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: Any,
        exc_info: Any,
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None,
    ) -> logging.LogRecord:
        # Create standard record
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)

        # Inspect call stack to find the module where logger.<level>() was invoked
        frame = inspect.currentframe()
        if frame and frame.f_back:
            # Step back out of logging internal machinery to the actual caller
            caller_frame: FrameType | None = frame.f_back
            while caller_frame and caller_frame.f_code.co_filename.endswith("logging/__init__.py"):
                caller_frame = caller_frame.f_back

            if caller_frame:
                module = inspect.getmodule(caller_frame)
                if module and module.__name__:
                    # Dynamically override the record name!
                    record.name = module.__name__

        return record


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(name="StrachyBot")
    logger.setLevel(level=level)

    # Prevent logs from leaking to the root logger (blocks duplicate/3rd-party root formatting)
    logger.propagate = False

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        console_handler.setLevel(level)

        logger.addHandler(console_handler)

    return logger


# Register custom logger class with Python's logging system
logging.setLoggerClass(ModuleLogger)

# Create singleton
logger: logging.Logger = setup_logger(level=logging.DEBUG)
