from ..utils.config import is_development_mode

if is_development_mode():
    LOCALE_DIR = "../../locales"
else:
    LOCALE_DIR = "locales"
