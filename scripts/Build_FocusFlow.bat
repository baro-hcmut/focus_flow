@echo off
chcp 65001 >nul
title Focus Flow - Release Build System
color 0b
cd /d "%~dp0\.."

echo.
echo  =============================================================
echo     ⚡ FOCUS FLOW - BUILD & EXPORT STANDALONE RELEASE
echo  =============================================================
echo.
echo  [1/3] Kiem tra moi truong dong goi (PyInstaller)...
pip install pyinstaller
echo.
echo  [2/3] Dang bien dich Focus Flow (UI Obsidian, Mini HUD, Lofi Audio)...
pyinstaller -y --noconsole --onedir --icon="assets\focus_flow_v2.ico" --paths="src" --add-data "web;web" --add-data "sounds;sounds" --add-data "assets;assets" --collect-all pythonnet --collect-all clr_loader --name="Focus Flow" --clean main.py

copy /y "Focus Flow.exe.config" "dist\Focus Flow\Focus Flow.exe.config" >nul
if exist "dist\Focus Flow\Chay_Focus_Flow.bat" copy /y "dist\Focus Flow\Chay_Focus_Flow.bat" "dist\Focus Flow\Chay_Focus_Flow.bat" >nul
if exist "dist\Focus Flow\Tao_Shortcut_Desktop.bat" copy /y "dist\Focus Flow\Tao_Shortcut_Desktop.bat" "dist\Focus Flow\Tao_Shortcut_Desktop.bat" >nul
if exist "dist\Focus Flow\Huong_Dan_Cho_Ban.txt" copy /y "dist\Focus Flow\Huong_Dan_Cho_Ban.txt" "dist\Focus Flow\Huong_Dan_Cho_Ban.txt" >nul
echo.
echo  [3/3] Xuat ban thanh cong!
echo.
echo  San pham doc lap nam tai: dist\Focus Flow\Focus Flow.exe
echo  =============================================================
echo.
pause
