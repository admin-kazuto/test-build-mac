#!/bin/bash
# Build script for macOS - Chạy trên macOS
# Chống dịch ngược với Nuitka (giống Windows)

set -e

echo "=========================================="
echo "Building Kuro Studio for macOS"
echo "=========================================="

# Kiểm tra macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "[!] Error: This script must be run on macOS!"
    exit 1
fi

# Kiểm tra Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "[!] Python 3.12 not found!"
    echo "[*] Installing Python 3.12..."
    brew install python@3.12 || {
        echo "[!] Please install Python 3.12 manually"
        exit 1
    }
fi

echo "[*] Using Python 3.12"
python3.12 --version

# Kiểm tra và cài đặt dependencies
echo ""
echo "[*] Checking dependencies..."

if ! python3.12 -m pip show nuitka &> /dev/null; then
    echo "[*] Installing Nuitka..."
    python3.12 -m pip install nuitka
fi

if ! python3.12 -m pip show PyQt6 &> /dev/null; then
    echo "[*] Installing PyQt6..."
    python3.12 -m pip install PyQt6
fi

if ! python3.12 -m pip show requests &> /dev/null; then
    echo "[*] Installing requests..."
    python3.12 -m pip install requests urllib3
fi

# Kiểm tra file input - Skip obfuscated file if it has syntax errors
if [ -f "run_server_obfuscated.py" ]; then
    # Verify obfuscated file is valid Python
    if python3.12 -m py_compile run_server_obfuscated.py 2>/dev/null; then
        echo "[*] Using obfuscated file: run_server_obfuscated.py"
        INPUT_FILE="run_server_obfuscated.py"
    else
        echo "[!] Obfuscated file has syntax errors, using original"
        INPUT_FILE="run_server.py"
    fi
else
    echo "[*] Using original file: run_server.py"
    INPUT_FILE="run_server.py"
fi

# Tạo thư mục dist
mkdir -p dist

echo ""
echo "[*] Starting Nuitka build for macOS..."
echo "[*] This may take 5-10 minutes..."
echo ""

# Build với Nuitka cho macOS - Tăng cường bảo mật
echo "[*] Building with Nuitka (security enhanced)..."
python3.12 -m nuitka \
    --standalone \
    --onefile \
    --macos-disable-console \
    --output-dir=dist \
    --output-filename=KuroStudio \
    --assume-yes-for-downloads \
    --enable-plugin=pyqt6 \
    --include-package-data=PyQt6 \
    --include-qt-plugins=qml \
    --nofollow-import-to=test,tests,unittest \
    --python-flag=-O \
    --python-flag=-OO \
    --no-pyi-file \
    "$INPUT_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Build failed!"
    exit 1
fi

# Copy ffmpeg nếu có
if [ -f "ffmpeg" ] || [ -f "ffmpeg.exe" ]; then
    echo ""
    echo "[*] Copying ffmpeg..."
    if [ -f "ffmpeg" ]; then
        cp "ffmpeg" "dist/"
    elif [ -f "ffmpeg.exe" ]; then
        # Nếu có ffmpeg.exe (Windows), cần ffmpeg cho Mac
        echo "[!] Warning: ffmpeg.exe is for Windows, need macOS version"
    fi
    echo "[+] ffmpeg copied"
fi

echo ""
echo "=========================================="
echo "[+] BUILD THÀNH CÔNG!"
echo "=========================================="
echo "[*] File: dist/KuroStudio"
echo "[*] Kích thước: $(du -h dist/KuroStudio | cut -f1)"
echo ""
echo "[+] Bảo vệ chống dịch ngược:"
echo "    - Native binary (không có Python bytecode)"
echo "    - Không có console window"
echo "    - Rất khó reverse engineering"
echo ""
echo "[*] Để tạo .app bundle, chạy:"
echo "    ./create_mac_app.sh"
echo ""

