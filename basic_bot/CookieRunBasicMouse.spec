# -*- mode: python ; coding: utf-8 -*-
import os
import re

# The exe name follows BOT_VERSION in bot_config.py (the updater relies on this name).
with open(os.path.join(SPECPATH, "bot_config.py"), encoding="utf-8") as _f:
    BOT_VERSION = re.search(r'^BOT_VERSION = "([^"]+)"', _f.read(), re.M).group(1)


a = Analysis(
    ["cookie_bot.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("buff_template.png", "."),
        ("play_template.png", "."),
        ("ok_template.png", "."),
        ("open_all.png", "."),
        ("confirm.png", "."),
        ("boots_screen.png", "."),
        ("option.png", "."),
        ("multi.png", "."),
        ("multi_buy.png", "."),
        ("double_coin.png", "."),
        ("base_speed.png", "."),
        ("magnet.png", "."),
        ("close_btn.png", "."),
        ("confirm_main_btn.png", "."),
        ("relay_bnt.png", "."),
        ("stop_btn.png", "."),
        ("img_bonus2.png", "."),
        ("quit_btn.png", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f"CookieRunBasicMouse_v{BOT_VERSION}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
