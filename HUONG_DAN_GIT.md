# Hướng Dẫn Setup Git và Build Mac App

## 🚀 Bước 1: Setup Git Repository

### Trên Windows:

1. **Chạy script tự động:**
   ```cmd
   setup_git.bat
   ```

2. **Hoặc làm thủ công:**
   ```cmd
   git init
   git add .
   git commit -m "Initial commit - Add Mac build support"
   git branch -M main
   git remote add origin https://github.com/admin-kazuto/test-build-mac.git
   git push -u origin main
   ```

### Trên Mac/Linux:

1. **Chạy script tự động:**
   ```bash
   chmod +x setup_git.sh
   ./setup_git.sh
   ```

2. **Hoặc làm thủ công:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Add Mac build support"
   git branch -M main
   git remote add origin https://github.com/admin-kazuto/test-build-mac.git
   git push -u origin main
   ```

## 🍎 Bước 2: Build Mac App với GitHub Actions

### Cách 1: Tự động (khi push code)

1. Push code lên GitHub:
   ```bash
   git add .
   git commit -m "Update code"
   git push
   ```

2. GitHub Actions sẽ tự động chạy (nếu có thay đổi trong `run_server.py` hoặc `build_mac.sh`)

### Cách 2: Chạy thủ công

1. Vào GitHub repository: https://github.com/admin-kazuto/test-build-mac

2. Click tab **"Actions"**

3. Chọn workflow **"Build macOS App"**

4. Click nút **"Run workflow"** (bên phải)

5. Chọn branch (thường là `main`)

6. Click **"Run workflow"**

7. Đợi build xong (5-10 phút)

8. Download artifact:
   - Click vào build job vừa chạy
   - Scroll xuống phần **"Artifacts"**
   - Click **"KuroStudio-macOS"** để download

## 📦 Kết quả

Sau khi download và giải nén, bạn sẽ có:

- **KuroStudio** - Executable file (native binary)
- **KuroStudio.app** - macOS app bundle (double-click để chạy)

## 🔧 Troubleshooting

### Lỗi: "Repository not found"
- Kiểm tra URL repository có đúng không
- Kiểm tra bạn có quyền truy cập repository không

### Lỗi: "Authentication failed"
- Cần setup GitHub Personal Access Token
- Hoặc dùng SSH key thay vì HTTPS

### Lỗi: "Workflow not found"
- Kiểm tra file `.github/workflows/build-mac.yml` đã được commit chưa
- Push lại code: `git push`

### Build thất bại trên GitHub Actions
- Xem log trong tab "Actions"
- Kiểm tra Python version và dependencies
- Thử chạy lại workflow

## 📝 Lưu ý

1. **GitHub Actions miễn phí** cho public repository
2. **Private repository** có giới hạn: 2000 phút/tháng
3. **Build time**: Thường mất 5-10 phút
4. **Artifact retention**: 30 ngày (có thể tăng trong workflow)

## 🎯 Tóm tắt

1. ✅ Setup git: `setup_git.bat` hoặc `setup_git.sh`
2. ✅ Push code: `git push`
3. ✅ Vào GitHub → Actions → Run workflow
4. ✅ Download artifact khi build xong
5. ✅ Có Mac app với bảo vệ chống reverse engineering!

