from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ["babel.dates", "babel.numbers"]

datas = collect_data_files("babel")
