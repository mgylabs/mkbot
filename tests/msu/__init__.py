import pathlib

current_file_path = pathlib.Path(__file__).parent.resolve()
project_root = pathlib.Path(current_file_path).parent.parent.resolve()
