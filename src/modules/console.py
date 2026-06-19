from datetime import datetime
from colorama import Fore

text_bold = "\033[1m"
text_underline = "\033[4m"
text_end = "\033[0m"
text_space = "\u1CBC"


def current_time() -> str:
    return (
        Fore.LIGHTBLACK_EX + text_bold +
        datetime.now().strftime("%Y-%m-%d %H:%M:%S") + text_end
    )


def log(category: str, message: str):
    category = " " + category
    while len(category) < 10:
        category += " "
    print(
        current_time() + Fore.GREEN + category +
        Fore.WHITE + message
    )
