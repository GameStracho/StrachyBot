import logging
import inspect
from typing import Any, Mapping
from types import FrameType


class ModuleLogger(logging.Logger):
    """Custom Logger that dynamically replaces record.name with the caller's module name."""

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
        console_handler.setLevel(level)

        # Apply your formatter
        formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)-8s %(message)s")
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


# Register custom logger class with Python's logging system
logging.setLoggerClass(ModuleLogger)

# Create singleton
logger: logging.Logger = setup_logger(level=logging.DEBUG)
