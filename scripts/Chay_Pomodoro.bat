@echo off
cd /d "%~dp0"
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw "%~dp0main.py"
) else (
    if exist "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe" (
        start "" "C:\Users\nhatb\AppData\Local\Programs\Python\Python314\pythonw.exe" "%~dp0main.py"
    ) else (
        start "" python "%~dp0main.py"
    )
)
