# ETime Android

安卓端使用 Capacitor 复用现有 React/Vite 前端，原生工程位于 `frontend/android`。

## 开发准备

- 安装 Node.js 依赖：`npm install`
- 安装 Android Studio，并准备 Android SDK / JDK 17+
- 后端需要允许 Capacitor WebView 来源：`http://localhost`（默认配置和 `.env.example` 已包含）

## API 地址

网页端默认继续使用 `/api/v1`，由 Vite 或 Nginx 代理到后端。

安卓端默认连接 `https://time.lally.top/api/v1`。如需连接自己的后端，构建前设置 `VITE_API_BASE_URL`：

```powershell
$env:VITE_API_BASE_URL = 'https://your-domain.example/api/v1'
npm run android:sync
```

## 常用命令

```powershell
# 同步最新网页产物到 Android 工程
npm run android:sync

# 打开 Android Studio
npm run android:open

# 构建 debug APK
npm run android:build:debug
```

debug APK 输出路径：

```text
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```
