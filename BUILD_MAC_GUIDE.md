# HƯỚNG DẪN BUILD MAC APP - CHỐNG DỊCH NGƯỢC

## ⚠️ VẤN ĐỀ: Bạn đang dùng Windows

**Nuitka KHÔNG hỗ trợ cross-compilation** - không thể build Mac app trên Windows.

## ✅ GIẢI PHÁP

### **Phương án 1: GitHub Actions (KHUYẾN NGHỊ)** ⭐

**Ưu điểm:**
- ✅ Miễn phí (public repo)
- ✅ Tự động build khi push code
- ✅ Không cần Mac
- ✅ Build trên macOS thật

**Cách dùng:**
1. Push code lên GitHub
2. File `.github/workflows/build-mac.yml` đã sẵn
3. Vào Actions tab → chọn "Build macOS App" → Run workflow
4. Đợi build xong → Download artifact

**Lệnh:**
```bash
git add .
git commit -m "Add Mac build"
git push
# Sau đó vào GitHub → Actions → Download artifact
```

---

### **Phương án 2: Mac thật / VM**

**Nếu có Mac hoặc VM:**

1. Copy code lên Mac
2. Chạy script:
```bash
chmod +x build_mac.sh
./build_mac.sh
```

3. Tạo .app bundle:
```bash
chmod +x create_mac_app.sh
./create_mac_app.sh
```

4. Kết quả: `dist/KuroStudio.app`

---

### **Phương án 3: Cloud Build Service**

**Các dịch vụ:**
- **MacStadium** (trả phí)
- **MacinCloud** (trả phí)
- **GitHub Actions** (miễn phí cho public repo) ⭐

---

## 📋 YÊU CẦU CHO MAC BUILD

### **Trên macOS:**
- Python 3.12
- Nuitka: `pip install nuitka`
- PyQt6: `pip install PyQt6`
- Xcode Command Line Tools

**Cài đặt:**
```bash
# Cài Xcode Command Line Tools
xcode-select --install

# Cài Python 3.12 (nếu chưa có)
brew install python@3.12

# Cài dependencies
python3.12 -m pip install nuitka PyQt6 requests urllib3
```

---

## 🔧 SCRIPT BUILD

### **1. build_mac.sh**
- Build executable với Nuitka
- Tương tự Windows nhưng cho macOS
- Option: `--macos-disable-console` (ẩn console)

### **2. create_mac_app.sh**
- Tạo .app bundle từ executable
- Tạo Info.plist
- Copy ffmpeg vào Resources

### **3. .github/workflows/build-mac.yml**
- GitHub Actions workflow
- Tự động build trên macOS
- Upload artifact để download

---

## 🚀 CÁCH DÙNG GITHUB ACTIONS

### **Bước 1: Push code lên GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

### **Bước 2: Kích hoạt Actions**
1. Vào GitHub repo
2. Tab "Actions"
3. Chọn "Build macOS App"
4. Click "Run workflow"
5. Chọn branch → Run

### **Bước 3: Download**
1. Đợi build xong (5-10 phút)
2. Click vào build job
3. Download artifact "KuroStudio-macOS"

---

## 📦 KẾT QUẢ BUILD

### **File output:**
- `dist/KuroStudio` - Executable (standalone)
- `dist/KuroStudio.app` - macOS app bundle

### **Bảo vệ:**
- ✅ Native binary (không có Python bytecode)
- ✅ Không có console window
- ✅ Rất khó reverse engineering
- ✅ Giống Windows build

---

## ⚙️ TÙY CHỌN BUILD

### **Nuitka options cho Mac:**
```bash
--standalone              # Standalone executable
--onefile                 # Single file
--macos-disable-console   # Ẩn console (giống --windows-disable-console)
--output-dir=dist         # Output directory
--output-filename=KuroStudio  # Tên file
--enable-plugin=pyqt6     # PyQt6 support
--include-package-data=PyQt6  # Include PyQt6 data
```

---

## 🎯 KHUYẾN NGHỊ

### **Nếu không có Mac:**
→ Dùng **GitHub Actions** (miễn phí, tự động)

### **Nếu có Mac:**
→ Chạy script trực tiếp (nhanh hơn)

### **Nếu cần build thường xuyên:**
→ Setup GitHub Actions (tự động mỗi khi push)

---

## 📝 LƯU Ý

1. **FFmpeg cho Mac:**
   - Cần bản macOS của ffmpeg
   - Download từ: https://ffmpeg.org/download.html
   - Hoặc: `brew install ffmpeg`

2. **Code signing (tùy chọn):**
   - Để phân phối trên Mac App Store
   - Cần Apple Developer account ($99/năm)
   - Không bắt buộc cho personal use

3. **Notarization (tùy chọn):**
   - Để tránh warning "unidentified developer"
   - Cần Apple Developer account
   - Không bắt buộc

---

## ✅ TÓM TẮT

**Bạn đang dùng Windows → Không thể build Mac app trực tiếp**

**Giải pháp tốt nhất:**
1. Push code lên GitHub
2. Dùng GitHub Actions (đã setup sẵn)
3. Download artifact khi build xong

**Hoặc:**
- Dùng Mac thật / VM
- Chạy `build_mac.sh`

**Kết quả:** Mac app với bảo vệ chống dịch ngược giống Windows! 🛡️

