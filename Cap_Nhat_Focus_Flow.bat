@echo off
chcp 65001 >nul
title Focus Flow - Trình Cập Nhật Tự Động 1-Click
color 0b

echo ======================================================================
echo             FOCUS FLOW • TRÌNH CẬP NHẬT TỰ ĐỘNG (1-CLICK)
echo ======================================================================
echo.

set "REPO=baro-hcmut/focus_flow"
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

echo [*] Đang kiểm tra phiên bản mới nhất từ GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference = 'SilentlyContinue';" ^
    "try {" ^
    "    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/%REPO%/releases/latest' -Headers @{'User-Agent'='FocusFlow-Updater'};" ^
    "    $tag = $release.tag_name;" ^
    "    $asset = $release.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1;" ^
    "    if (-not $asset) { Write-Output 'ERROR: Không tìm thấy file zip cài đặt trên GitHub.'; exit 1 }" ^
    "    Write-Output \"TAG=$tag\";" ^
    "    Write-Output \"URL=$($asset.browser_download_url)\";" ^
    "    Write-Output \"NAME=$($asset.name)\";" ^
    "} catch {" ^
    "    Write-Output \"ERROR: $($_.Exception.Message)\";" ^
    "    exit 1" ^
    "}" > "%TEMP%\focus_flow_release_info.txt"

if %ERRORLEVEL% NEQ 0 (
    echo [!] Lỗi khi kết nối GitHub. Vui lòng kiểm tra lại kết nối mạng.
    type "%TEMP%\focus_flow_release_info.txt"
    del "%TEMP%\focus_flow_release_info.txt" 2>nul
    echo.
    pause
    exit /b 1
)

for /f "tokens=1,* delims==" %%A in ('type "%TEMP%\focus_flow_release_info.txt"') do (
    if "%%A"=="TAG" set "LATEST_TAG=%%B"
    if "%%A"=="URL" set "DOWNLOAD_URL=%%B"
    if "%%A"=="NAME" set "ASSET_NAME=%%B"
    if "%%A"=="ERROR" set "ERR_MSG=%%B"
)
del "%TEMP%\focus_flow_release_info.txt" 2>nul

if not defined DOWNLOAD_URL (
    echo [!] %ERR_MSG%
    pause
    exit /b 1
)

echo [+] Phiên bản mới nhất trên GitHub: %LATEST_TAG%
echo [+] Đang chuẩn bị tải gói cài đặt...
echo.

:: Đóng ứng dụng Focus Flow nếu đang chạy
taskkill /f /im "Focus Flow.exe" 2>nul
timeout /t 1 /nobreak >nul

set "TEMP_DIR=%TEMP%\focus_flow_auto_update"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"
set "ZIP_FILE=%TEMP_DIR%\update.zip"

echo [*] Đang tải bản cập nhật %LATEST_TAG% (Vui lòng chờ trong giây lát)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference = 'Continue';" ^
    "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_FILE%' -UserAgent 'FocusFlow-Updater'"

if not exist "%ZIP_FILE%" (
    echo [!] Lỗi: Không thể tải file cập nhật.
    pause
    exit /b 1
)

echo [*] Đang giải nén tập tin...
set "EXTRACT_DIR=%TEMP_DIR%\extracted"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"

:: Tìm thư mục chứa Focus Flow.exe trong gói giải nén
set "PAYLOAD_DIR=%EXTRACT_DIR%"
if not exist "%PAYLOAD_DIR%\Focus Flow.exe" (
    for /d %%D in ("%EXTRACT_DIR%\*") do (
        if exist "%%D\Focus Flow.exe" set "PAYLOAD_DIR=%%D"
    )
)

echo [*] Sao lưu dữ liệu & cài đặt mới...
set "BACKUP_DIR=%TEMP%\focus_flow_backup"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if exist "%APP_DIR%\config.json" copy /y "%APP_DIR%\config.json" "%BACKUP_DIR%\" >nul

xcopy /s /e /y /q "%PAYLOAD_DIR%\*" "%APP_DIR%\" >nul

if exist "%BACKUP_DIR%\config.json" copy /y "%BACKUP_DIR%\config.json" "%APP_DIR%\" >nul
rmdir /s /q "%BACKUP_DIR%" 2>nul

:: Bỏ chặn Windows Defender SmartScreen / Zone.Identifier
powershell -NoProfile -Command "Get-ChildItem -Path '%APP_DIR%' -Recurse | Unblock-File -ErrorAction SilentlyContinue" 2>nul

:: Dọn dẹp thư mục tạm
rmdir /s /q "%TEMP_DIR%" 2>nul

echo.
echo ======================================================================
echo    🎉 CHÚC MỪNG! BẠN ĐÃ CẬP NHẬT LÊN %LATEST_TAG% THÀNH CÔNG!
echo ======================================================================
echo [*] Đang tự động mở Focus Flow...
start "" "%APP_DIR%\Focus Flow.exe"

timeout /t 3 /nobreak >nul
exit

