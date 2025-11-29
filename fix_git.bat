@echo off
setlocal enabledelayedexpansion
REM Script để fix git - unstage extracted files và push lại

echo ==========================================
echo Fix Git - Remove Extracted Files
echo ==========================================

REM Unstage extracted files
echo.
echo [*] Removing extracted files from staging...
git reset HEAD -- "KuroStudio.exe_extracted/" 2>nul
if %errorlevel% equ 0 (
    echo [+] Đã unstage extracted files
) else (
    echo [*] Không có extracted files trong staging
)

REM Kiểm tra branch hiện tại
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i

if "!CURRENT_BRANCH!"=="" (
    echo.
    echo [*] Tạo branch main...
    git checkout -b main 2>nul
    if %errorlevel% neq 0 (
        git branch -M main
    )
    set CURRENT_BRANCH=main
)

echo.
echo [*] Branch hiện tại: !CURRENT_BRANCH!

REM Kiểm tra remote
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [*] Thêm remote origin...
    set /p remote_url="Nhập GitHub repository URL: "
    if "!remote_url!"=="" (
        set remote_url=https://github.com/admin-kazuto/test-build-mac.git
    )
    git remote add origin "!remote_url!"
    echo [+] Remote đã được thêm
)

REM Push
echo.
echo [*] Pushing to GitHub...
git push -u origin !CURRENT_BRANCH!

if %errorlevel% equ 0 (
    echo.
    echo [+] Push thành công!
    echo.
    echo ==========================================
    echo [+] HOÀN TẤT!
    echo ==========================================
    for /f "tokens=*" %%i in ('git remote get-url origin') do echo [*] Repository: %%i
    echo [*] Branch: !CURRENT_BRANCH!
) else (
    echo.
    echo [!] Push thất bại!
    echo [*] Có thể cần authenticate với GitHub
    echo [*] Thử chạy: git push -u origin !CURRENT_BRANCH!
)

pause

