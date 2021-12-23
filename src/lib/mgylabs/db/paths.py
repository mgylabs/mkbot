from ..utils.config import USER_DATA_PATH, is_development_mode

DB_URL = f"sqlite:///{USER_DATA_PATH}\\data.db"
if is_development_mode():
    SCRIPT_DIR = "../../migrations"
else:
    SCRIPT_DIR = "migrations"
