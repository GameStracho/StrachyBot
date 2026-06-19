from datetime import datetime
from colorama import Fore, Style
import sys

def current_time() -> str:
    return (
        Fore.LIGHTBLACK_EX + Style.BRIGHT
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + Style.RESET_ALL
    )


def log(category: str, color: str, message: str, file = sys.stdout) -> None:
    """print colored category followed by message to file"""

    padded_category = " " + category

    while len(padded_category) < 10:
        padded_category += " "

    print(current_time() + color + padded_category
        + Style.RESET_ALL + message,
        file
    )


def log_info(message: str) -> None:
    """print INFO message to stdout"""
    log("INFO", Fore.BLUE, message)


def log_error(message: str) -> None:
    """print ERROR message to stderr"""
    log("ERROR", Fore.RED, message, sys.stderr)


def log_warning(message: str) -> None:
    """print WARNING message to stdout"""
    log("WARNING", Fore.YELLOW, message)


def log_success(message: str) -> None:
    """print SUCCESS message to stdout"""
    log("SUCCESS", Fore.GREEN, message)


def log_debug(message: str) -> None:
    """print DEBUG message to stdout"""
    log("DEBUG", Fore.CYAN, message)


def highlight(style: str, text: str) -> str:
    """Apply style (color, bold, etc.) to text for prints"""
    return style + text + Style.RESET_ALL
