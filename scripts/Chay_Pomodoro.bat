@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%SCRIPT_DIR%..\main.py"
) else (
    if exist "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe" (
        start "" "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe" "%SCRIPT_DIR%..\main.py"
    ) else (
        start "" python "%SCRIPT_DIR%..\main.py"
    )
)
