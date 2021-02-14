# -*- mode: python ; coding: utf-8 -*-
import os
import sys
sys.path.append(os.curdir)
from core_ext import core_extensions

block_cipher = None

a = Analysis(['app.py'],
             pathex=[os.curdir],
             binaries=[],
             datas=[],
             hiddenimports=[*core_extensions],
             hookspath=['..\\hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          icon=os.getenv('CI_PROJECT_DIR') +
          '\\resources\\console\\mkbot_on.ico',
          upx=True,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='app')
