# Kuro Studio - Mac Build

Ứng dụng Kuro Studio được build cho macOS với Nuitka để bảo vệ chống reverse engineering.

## 🚀 Cách Build cho Mac

### Phương án 1: GitHub Actions (Khuyến nghị - Không cần Mac)

1. **Push code lên GitHub:**
   ```bash
   git add .
   git commit -m "Add Mac build support"
   git remote add origin https://github.com/admin-kazuto/test-build-mac.git
   git branch -M main
   git push -u origin main
   ```

2. **Chạy GitHub Actions:**
   - Vào tab "Actions" trên GitHub
   - Chọn workflow "Build macOS App"
   - Click "Run workflow"
   - Đợi build xong (5-10 phút)
   - Download artifact "KuroStudio-macOS"

### Phương án 2: Build trên Mac thật

1. **Cài đặt dependencies:**
   ```bash
   # Cài Xcode Command Line Tools
   xcode-select --install
   
   # Cài Python 3.12
   brew install python@3.12
   
   # Cài dependencies
   python3.12 -m pip install nuitka PyQt6 requests urllib3
   ```

2. **Obfuscate code (tùy chọn - tăng bảo mật):**
   ```bash
   python3.12 obfuscate.py run_server.py run_server_obfuscated.py
   ```

3. **Build với Nuitka:**
   ```bash
   chmod +x build_mac.sh
   ./build_mac.sh
   ```

4. **Tạo .app bundle:**
   ```bash
   chmod +x create_mac_app.sh
   ./create_mac_app.sh
   ```

5. **Kết quả:**
   - `dist/KuroStudio` - Executable
   - `dist/KuroStudio.app` - macOS app bundle

## 🛡️ Bảo vệ Chống Reverse Engineering

### Tính năng bảo mật:

1. **Nuitka Compilation:**
   - ✅ Compile Python → C++ → Native binary
   - ✅ Không có Python bytecode
   - ✅ Rất khó reverse engineering

2. **Code Obfuscation (tùy chọn):**
   - ✅ Đổi tên biến/function/class
   - ✅ Encode strings (base64, hex)
   - ✅ Thêm dead code

3. **Optimization:**
   - ✅ `-O` flag: Remove assertions, docstrings
   - ✅ `-OO` flag: Additional optimization
   - ✅ `--no-pyi-file`: Không tạo .pyi files

4. **macOS Specific:**
   - ✅ `--macos-disable-console`: Ẩn console window
   - ✅ Native binary cho macOS

## 📋 Yêu cầu

- Python 3.12
- Nuitka: `pip install nuitka`
- PyQt6: `pip install PyQt6`
- Xcode Command Line Tools (trên Mac)

## 📦 Kết quả Build

Sau khi build thành công, bạn sẽ có:

- **KuroStudio** - Standalone executable (native binary)
- **KuroStudio.app** - macOS app bundle (có thể double-click để chạy)

## 🔧 Troubleshooting

### Lỗi: "Python 3.12 not found"
```bash
brew install python@3.12
```

### Lỗi: "Xcode Command Line Tools not found"
```bash
xcode-select --install
```

### Lỗi: "Nuitka build failed"
- Kiểm tra Python version: `python3.12 --version`
- Cài lại Nuitka: `python3.12 -m pip install --upgrade nuitka`

## 📝 Lưu ý

1. **FFmpeg cho Mac:**
   - Cần bản macOS của ffmpeg
   - Download từ: https://ffmpeg.org/download.html
   - Hoặc: `brew install ffmpeg`

2. **Code Signing (tùy chọn):**
   - Để phân phối trên Mac App Store
   - Cần Apple Developer account ($99/năm)
   - Không bắt buộc cho personal use

3. **Notarization (tùy chọn):**
   - Để tránh warning "unidentified developer"
   - Cần Apple Developer account
   - Không bắt buộc

## 🎯 So sánh với Windows Build

| Tính năng | Windows | macOS |
|-----------|---------|-------|
| Nuitka | ✅ | ✅ |
| Obfuscation | ✅ | ✅ |
| Native binary | ✅ | ✅ |
| Console hidden | ✅ | ✅ |
| .app bundle | ❌ | ✅ |

## 📚 Tài liệu thêm

- [BUILD_MAC_GUIDE.md](BUILD_MAC_GUIDE.md) - Hướng dẫn chi tiết
- [NUITKA_SECURITY.md](NUITKA_SECURITY.md) - Thông tin bảo mật
- [README_BUILD.md](README_BUILD.md) - Hướng dẫn build tổng quát

