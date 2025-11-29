@echo off
setlocal enabledelayedexpansion
REM Script để setup git và push code lên GitHub (Windows)

echo ==========================================
echo Git Setup Script
echo ==========================================

REM Kiểm tra git đã được cài chưa
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git chưa được cài đặt!
    echo [*] Vui lòng cài Git: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo [*] Git version:
git --version

REM Kiểm tra đã có git repo chưa
if not exist ".git" (
    echo.
    echo [*] Khởi tạo git repository...
    git init
    echo [+] Git repository đã được khởi tạo
)

REM Kiểm tra remote
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [*] Chưa có remote origin
    echo [*] Thêm remote origin...
    echo.
    set /p user_url="Nhập GitHub repository URL (hoặc Enter để dùng mặc định): "
    
    if "!user_url!"=="" (
        set user_url=https://github.com/admin-kazuto/test-build-mac.git
    )
    
    git remote add origin "!user_url!" 2>nul
    if %errorlevel% neq 0 (
        echo [!] Remote đã tồn tại hoặc URL không hợp lệ
        echo [*] Để thay đổi remote: git remote set-url origin ^<URL^>
    ) else (
        echo [+] Remote origin đã được thêm: !user_url!
    )
) else (
    echo.
    for /f "tokens=*" %%i in ('git remote get-url origin') do set REMOTE_URL=%%i
    echo [*] Remote origin hiện tại: !REMOTE_URL!
    set /p change_remote="Bạn có muốn thay đổi remote? (y/N): "
    if /i "!change_remote!"=="y" (
        set /p new_url="Nhập GitHub repository URL mới: "
        git remote set-url origin "!new_url!"
        echo [+] Remote đã được cập nhật: !new_url!
    )
)

REM Kiểm tra branch
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i

if "!CURRENT_BRANCH!"=="" (
    echo.
    echo [*] Tạo branch main...
    git checkout -b main 2>nul
    if %errorlevel% neq 0 (
        git branch -M main
    )
    echo [+] Branch main đã được tạo
) else (
    echo.
    echo [*] Branch hiện tại: !CURRENT_BRANCH!
    if not "!CURRENT_BRANCH!"=="main" if not "!CURRENT_BRANCH!"=="master" (
        set /p change_branch="Bạn có muốn đổi sang branch main? (y/N): "
        if /i "!change_branch!"=="y" (
            git checkout -b main 2>nul
            if %errorlevel% neq 0 (
                git branch -M main
            )
            echo [+] Đã chuyển sang branch main
        )
    )
)

REM Add và commit
echo.
echo [*] Kiểm tra file changes...
git status --short

echo.
set /p do_commit="Bạn có muốn add tất cả file và commit? (Y/n): "

if /i not "!do_commit!"=="n" (
    echo.
    echo [*] Adding files...
    git add .
    
    echo.
    set /p commit_msg="Nhập commit message (hoặc Enter để dùng mặc định): "
    
    if "!commit_msg!"=="" (
        set commit_msg=Initial commit - Add Mac build support
    )
    
    echo.
    echo [*] Committing...
    git commit -m "!commit_msg!"
    echo [+] Commit thành công!
)

REM Push
echo.
set /p do_push="Bạn có muốn push lên GitHub? (Y/n): "

if /i not "!do_push!"=="n" (
    echo.
    echo [*] Pushing to GitHub...
    
    for /f "tokens=*" %%i in ('git branch --show-current') do set BRANCH_NAME=%%i
    git push -u origin "!BRANCH_NAME!"
    
    if %errorlevel% neq 0 (
        echo.
        echo [!] Push thất bại!
        echo [*] Có thể cần authenticate với GitHub
        echo [*] Hoặc chạy: git push -u origin !BRANCH_NAME!
    ) else (
        echo.
        echo [+] Push thành công!
        echo.
        echo ==========================================
        echo [+] HOÀN TẤT!
        echo ==========================================
        for /f "tokens=*" %%i in ('git remote get-url origin') do echo [*] Repository: %%i
        echo [*] Branch: !BRANCH_NAME!
        echo.
        echo [*] Để build Mac app:
        echo     1. Vào GitHub -^> Actions
        echo     2. Chọn 'Build macOS App'
        echo     3. Click 'Run workflow'
        echo     4. Đợi build xong và download artifact
        echo.
    )
)

pause

