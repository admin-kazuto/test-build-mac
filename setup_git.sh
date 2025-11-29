#!/bin/bash
# Script để setup git và push code lên GitHub

set -e

echo "=========================================="
echo "Git Setup Script"
echo "=========================================="

# Kiểm tra git đã được cài chưa
if ! command -v git &> /dev/null; then
    echo "[!] Git chưa được cài đặt!"
    echo "[*] Vui lòng cài Git: https://git-scm.com/downloads"
    exit 1
fi

echo "[*] Git version: $(git --version)"

# Kiểm tra đã có git repo chưa
if [ ! -d ".git" ]; then
    echo ""
    echo "[*] Khởi tạo git repository..."
    git init
    echo "[+] Git repository đã được khởi tạo"
fi

# Kiểm tra remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE_URL" ]; then
    echo ""
    echo "[*] Chưa có remote origin"
    echo "[*] Thêm remote origin..."
    echo ""
    read -p "Nhập GitHub repository URL (hoặc Enter để dùng mặc định): " user_url
    
    if [ -z "$user_url" ]; then
        user_url="https://github.com/admin-kazuto/test-build-mac.git"
    fi
    
    git remote add origin "$user_url" 2>/dev/null || {
        echo "[!] Remote đã tồn tại hoặc URL không hợp lệ"
        echo "[*] Để thay đổi remote: git remote set-url origin <URL>"
    }
    echo "[+] Remote origin đã được thêm: $user_url"
else
    echo ""
    echo "[*] Remote origin hiện tại: $REMOTE_URL"
    read -p "Bạn có muốn thay đổi remote? (y/N): " change_remote
    if [[ "$change_remote" =~ ^[Yy]$ ]]; then
        read -p "Nhập GitHub repository URL mới: " new_url
        git remote set-url origin "$new_url"
        echo "[+] Remote đã được cập nhật: $new_url"
    fi
fi

# Kiểm tra branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [ -z "$CURRENT_BRANCH" ]; then
    echo ""
    echo "[*] Tạo branch main..."
    git checkout -b main 2>/dev/null || git branch -M main
    echo "[+] Branch main đã được tạo"
else
    echo ""
    echo "[*] Branch hiện tại: $CURRENT_BRANCH"
    if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
        read -p "Bạn có muốn đổi sang branch main? (y/N): " change_branch
        if [[ "$change_branch" =~ ^[Yy]$ ]]; then
            git checkout -b main 2>/dev/null || git branch -M main
            echo "[+] Đã chuyển sang branch main"
        fi
    fi
fi

# Add và commit
echo ""
echo "[*] Kiểm tra file changes..."
git status --short

echo ""
read -p "Bạn có muốn add tất cả file và commit? (Y/n): " do_commit

if [[ ! "$do_commit" =~ ^[Nn]$ ]]; then
    echo ""
    echo "[*] Adding files..."
    git add .
    
    echo ""
    read -p "Nhập commit message (hoặc Enter để dùng mặc định): " commit_msg
    
    if [ -z "$commit_msg" ]; then
        commit_msg="Initial commit - Add Mac build support"
    fi
    
    echo ""
    echo "[*] Committing..."
    git commit -m "$commit_msg"
    echo "[+] Commit thành công!"
fi

# Push
echo ""
read -p "Bạn có muốn push lên GitHub? (Y/n): " do_push

if [[ ! "$do_push" =~ ^[Nn]$ ]]; then
    echo ""
    echo "[*] Pushing to GitHub..."
    
    BRANCH_NAME=$(git branch --show-current)
    git push -u origin "$BRANCH_NAME" || {
        echo ""
        echo "[!] Push thất bại!"
        echo "[*] Có thể cần authenticate với GitHub"
        echo "[*] Hoặc chạy: git push -u origin $BRANCH_NAME"
    }
    
    echo ""
    echo "[+] Push thành công!"
    echo ""
    echo "=========================================="
    echo "[+] HOÀN TẤT!"
    echo "=========================================="
    echo "[*] Repository: $(git remote get-url origin)"
    echo "[*] Branch: $BRANCH_NAME"
    echo ""
    echo "[*] Để build Mac app:"
    echo "    1. Vào GitHub → Actions"
    echo "    2. Chọn 'Build macOS App'"
    echo "    3. Click 'Run workflow'"
    echo "    4. Đợi build xong và download artifact"
    echo ""
fi

