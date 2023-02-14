# -*- mode: python ; coding: utf-8 -*-
import os
import sys

sys.path.append(os.curdir)
from discord_ext import discord_extensions

block_cipher = None

core_a = Analysis(
    ["main.py"],
    pathex=[os.curdir, "..\\lib"],
    binaries=[],
    datas=[],
    hiddenimports=[*discord_extensions],
    hookspath=["..\\hooks"],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
core_pyz = PYZ(core_a.pure, core_a.zipped_data, cipher=block_cipher)
core_exe = EXE(
    core_pyz,
    core_a.scripts,
    [],
    exclude_binaries=True,
    name="MKBotCore",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    icon=os.getenv("CI_PROJECT_DIR") + "\\resources\\package\\mkbot.ico",
    upx=True,
    console=True,
)

msu_a = Analysis(
    ["../msu/msu.py"],
    pathex=["../msu", "..\\lib"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
msu_pyz = PYZ(msu_a.pure, msu_a.zipped_data, cipher=block_cipher)
msu_exe = EXE(
    msu_pyz,
    msu_a.scripts,
    [],
    exclude_binaries=True,
    name="msu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=os.getenv("CI_PROJECT_DIR") + "\\resources\\package\\mkbot.ico",
)

coll = COLLECT(
    core_exe,
    core_a.binaries,
    core_a.zipfiles,
    core_a.datas,
    msu_exe,
    msu_a.binaries,
    msu_a.zipfiles,
    msu_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="bin",
)
