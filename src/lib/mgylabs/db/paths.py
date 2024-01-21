from ..utils.config import USER_DATA_PATH, is_development_mode

DB_FILE = f"{USER_DATA_PATH}/data.db"
DB_URL = f"sqlite:///{DB_FILE}"
if is_development_mode():
    SCRIPT_DIR = "../../migrations"
else:
    SCRIPT_DIR = "migrations"
