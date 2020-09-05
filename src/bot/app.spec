# -*- mode: python ; coding: utf-8 -*-
import os
import sys
sys.path.append(os.curdir)
from core_ext import core_extensions

block_cipher = None

a = Analysis(['app.py'],
             pathex=[os.curdir],
             binaries=[(os.getenv('botpackage') +
                        '\\discord\\bin\\libopus-0.x64.dll', '.')],
             datas=[(os.getenv('botpackage') +
                     '\\langdetect\\utils\\messages.properties', 'langdetect\\utils'),
                    (os.getenv('botpackage') +
                     '\\langdetect\\profiles', 'langdetect\\profiles'),
                    (os.getenv('botpackage') + '\\mulgyeol_oauth\\static',
                     'mulgyeol_oauth\\static'),
                    (os.getenv('botpackage') + '\\mulgyeol_oauth\\templates', 'mulgyeol_oauth\\templates')],
             hiddenimports=["_cffi_backend", *core_extensions],
             hookspath=[],
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
          '\\src\\console\\Resources\\mkbot_on.ico',
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
