@echo off
setlocal
cd /d "%~dp0"
set SCRIPT_DIR=%~dp0
set TARGET=%SCRIPT_DIR%Chay_Pomodoro_Khong_Hien_Console.vbs
set ICON=%SCRIPT_DIR%focus_flow_v2.ico

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $desk = [Environment]::GetFolderPath('Desktop'); $old = Join-Path $desk 'Focus Flow - Pomodoro 50-10.lnk'; if (Test-Path $old) { Remove-Item $old -Force }; $s = $ws.CreateShortcut((Join-Path $desk 'Focus Flow.lnk')); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = '%ICON%'; $s.Description = ''; $s.Save(); [void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [void][System.Runtime.InteropServices.Marshal]"

ie4uinit.exe -show
echo [OK] Da cap nhat Shortcut Focus Flow voi logo moi cuc net ngoai Desktop!
pause
