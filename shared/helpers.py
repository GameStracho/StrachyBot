import unicodedata


def strip_accents(text: str) -> str:
    """Normalizes string by removing diacritical marks/accents in Python."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
