from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ["mecab", "mecab_ko_dic"]

datas = collect_data_files("mkbot_nlu")
datas += collect_data_files("mecab")
datas += collect_data_files("mecab_ko_dic")

binaries = [("C:/Windows/System32/msvcp140_1.dll", ".")]
