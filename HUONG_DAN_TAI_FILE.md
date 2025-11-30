# Hướng Dẫn Tải File Mac App

## 📦 File Build Xong Nằm Ở Đâu?

Sau khi build thành công trên GitHub Actions, file sẽ nằm trong **Artifacts**.

## 🔽 Cách Tải File Từ GitHub Actions

### Bước 1: Vào GitHub Actions
1. Vào repository: https://github.com/admin-kazuto/test-build-mac
2. Click tab **"Actions"**
3. Tìm workflow run đã thành công (có dấu ✅ xanh)
4. Click vào workflow run đó

### Bước 2: Download Artifact
1. Scroll xuống phần **"Artifacts"** (ở cuối trang)
2. Bạn sẽ thấy artifact tên **"KuroStudio-macOS"**
3. Click vào artifact để download
4. File sẽ được tải về dưới dạng `.zip`

### Bước 3: Giải Nén
1. Giải nén file `.zip` vừa tải
2. Bên trong sẽ có:
   - `KuroStudio` - Executable file
   - `KuroStudio.app` - macOS app bundle (double-click để chạy)

## ☁️ Upload Lên Google Drive

### Cách 1: Upload Thủ Công
1. Tải file từ GitHub Actions (theo hướng dẫn trên)
2. Vào Google Drive: https://drive.google.com
3. Upload file `.zip` hoặc `KuroStudio.app`
4. Share link cho người khác tải về

### Cách 2: Tự Động Upload (Khuyến Nghị) ⭐
GitHub Actions sẽ tự động upload lên Google Drive sau khi build xong!

**Cách setup:**
1. Tạo Google Drive API credentials (xem file `SETUP_GOOGLE_DRIVE.md`)
2. Thêm secrets vào GitHub repository
3. Workflow sẽ tự động upload sau mỗi build thành công

## 📱 Cách Dùng Trên Mac

1. **Tải file từ GitHub Actions hoặc Google Drive**
2. **Giải nén** (nếu là .zip)
3. **Double-click `KuroStudio.app`** để chạy
4. **Nếu bị warning "unidentified developer":**
   - Right-click → Open
   - Hoặc vào System Settings → Privacy & Security → Allow

## 🔗 Link Trực Tiếp

Sau khi setup Google Drive auto-upload, bạn sẽ có link trực tiếp để share:
- Link Google Drive (public hoặc với quyền truy cập)
- Có thể embed vào website
- Dễ dàng update version mới

