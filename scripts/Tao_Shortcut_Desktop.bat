@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "ROOT_DIR=%CD%"
popd

set "TARGET=%SCRIPT_DIR%Chay_Pomodoro_Khong_Hien_Console.vbs"
set "ICON=%ROOT_DIR%\assets\focus_flow_v2.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$targets = @([Environment]::GetFolderPath('Desktop'), [System.IO.Path]::Combine($env:USERPROFILE, 'OneDrive', 'Desktop'), [System.IO.Path]::Combine($env:USERPROFILE, 'Desktop')) | Select-Object -Unique; " ^
    "foreach ($d in $targets) { " ^
    "    if (Test-Path $d) { " ^
    "        $old = Join-Path $d 'Focus Flow - Pomodoro 50-10.lnk'; " ^
    "        if (Test-Path $old) { Remove-Item $old -Force -ErrorAction SilentlyContinue }; " ^
    "        $s = $ws.CreateShortcut((Join-Path $d 'Focus Flow.lnk')); " ^
    "        $s.TargetPath = '%TARGET%'; " ^
    "        $s.WorkingDirectory = '%ROOT_DIR%'; " ^
    "        $s.IconLocation = '%ICON%,0'; " ^
    "        $s.Save(); " ^
    "    } " ^
    "}"

ie4uinit.exe -show
echo [OK] Da cap nhat Shortcut Focus Flow voi logo sieu net ngoai Desktop!
pause
