#!/bin/bash
# Tạo macOS .app bundle từ Nuitka executable

set -e

echo "=========================================="
echo "Creating macOS .app Bundle"
echo "=========================================="

if [ ! -f "dist/KuroStudio" ]; then
    echo "[!] Error: dist/KuroStudio not found!"
    echo "[*] Please run build_mac.sh first"
    exit 1
fi

APP_NAME="KuroStudio"
APP_DIR="dist/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Tạo cấu trúc .app bundle
echo "[*] Creating .app bundle structure..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy executable
echo "[*] Copying executable..."
cp "dist/KuroStudio" "$MACOS_DIR/$APP_NAME"
chmod +x "$MACOS_DIR/$APP_NAME"

# Copy ffmpeg nếu có
if [ -f "dist/ffmpeg" ]; then
    echo "[*] Copying ffmpeg..."
    cp "dist/ffmpeg" "$RESOURCES_DIR/"
    chmod +x "$RESOURCES_DIR/ffmpeg"
fi

# Tạo Info.plist
echo "[*] Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.kurostudio.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0.3</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.3</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

echo ""
echo "=========================================="
echo "[+] .app Bundle Created!"
echo "=========================================="
echo "[*] Location: $APP_DIR"
echo "[*] Size: $(du -sh "$APP_DIR" | cut -f1)"
echo ""
echo "[*] To run:"
echo "    open $APP_DIR"
echo ""
echo "[*] To create DMG installer:"
echo "    ./create_dmg.sh"
echo ""

