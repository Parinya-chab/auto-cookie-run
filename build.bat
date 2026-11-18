@echo off
REM Build the bot into a single .exe (output: basic_bot\dist)
cd /d "%~dp0basic_bot"
pyinstaller --noconfirm CookieRunBasicMouse.spec
