import os
import pathlib

current_file_path = pathlib.Path(__file__).parent.resolve()
project_root = pathlib.Path(current_file_path).parent.resolve()

os.chdir(f"{project_root}/tests/bot")
print("> SET CHDIR:", os.getcwd())
