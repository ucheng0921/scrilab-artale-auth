# Artale Script Authentication Service

安全的 Firebase 認證服務，部署在 Render.com 上。

## 功能特點
- 🔐 安全的用戶認證
- 🔄 會話管理
- 🚀 速率限制
- 📊 健康檢查
- 🛡️ CORS 支援

## 部署說明
1. 設置 Render 環境變數
2. 部署到 Render
3. 更新客戶端配置

## 環境變數
- `FIREBASE_CREDENTIALS_BASE64`: Firebase 憑證（Base64 編碼）
- `APP_SECRET_KEY`: 應用密鑰
- `FLASK_ENV`: 環境設置
- `SESSION_TIMEOUT`: 會話超時時間

## API 端點
- `GET /health`: 健康檢查
- `POST /auth/login`: 用戶登入
- `POST /auth/logout`: 用戶登出
- `POST /auth/validate`: 會話驗證
