# Setup Tự Động Upload Lên Google Drive

## 🎯 Mục Đích

Tự động upload Mac app lên Google Drive sau mỗi lần build thành công trên GitHub Actions.

## 📋 Bước 1: Tạo Google Drive API Credentials

### 1.1. Tạo Google Cloud Project

1. Vào: https://console.cloud.google.com/
2. Tạo project mới (hoặc chọn project có sẵn)
3. Đặt tên: `kurostudio-mac-build`

### 1.2. Enable Google Drive API

1. Vào **APIs & Services** → **Library**
2. Tìm **"Google Drive API"**
3. Click **Enable**

### 1.3. Tạo Service Account

1. Vào **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Điền thông tin:
   - Name: `github-actions-uploader`
   - Description: `Upload Mac app to Google Drive`
4. Click **Create and Continue**
5. Skip role assignment → **Done**

### 1.4. Tạo Key cho Service Account

1. Click vào service account vừa tạo
2. Tab **Keys** → **Add Key** → **Create new key**
3. Chọn **JSON**
4. Download file JSON (lưu lại, sẽ cần sau)

### 1.5. Share Google Drive Folder

1. Tạo folder trên Google Drive (hoặc dùng folder có sẵn)
2. Right-click folder → **Share**
3. Thêm email của service account (tìm trong file JSON: `client_email`)
4. Cho quyền **Editor**

## 📋 Bước 2: Setup GitHub Secrets

1. Vào GitHub repository: https://github.com/admin-kazuto/test-build-mac
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Thêm các secrets sau:

### Secret 1: `GDRIVE_SERVICE_ACCOUNT`
- **Name:** `GDRIVE_SERVICE_ACCOUNT`
- **Value:** Copy toàn bộ nội dung file JSON vừa download

### Secret 2: `GDRIVE_FOLDER_ID` (Optional)
- **Name:** `GDRIVE_FOLDER_ID`
- **Value:** ID của folder Google Drive (lấy từ URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`)

## 📋 Bước 3: Cập Nhật Workflow

Workflow đã được cập nhật tự động! Chỉ cần thêm secrets là xong.

## ✅ Kiểm Tra

Sau khi setup xong:
1. Chạy workflow trên GitHub Actions
2. Sau khi build thành công, file sẽ tự động upload lên Google Drive
3. Check folder Google Drive để xác nhận

## 🔗 Lấy Link Share

1. Vào Google Drive folder
2. Right-click file → **Get link**
3. Chọn **Anyone with the link** → **Viewer**
4. Copy link và share

## 📝 Lưu Ý

- File sẽ được upload với tên: `KuroStudio-macOS-YYYYMMDD-HHMMSS.zip`
- Mỗi lần build sẽ tạo file mới (không ghi đè)
- Có thể xóa file cũ thủ công nếu cần

