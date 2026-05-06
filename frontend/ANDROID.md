# ETime Android

安卓端使用 Capacitor 复用现有 React/Vite 前端，原生工程位于 `frontend/android`。

## 开发准备

- 安装 Node.js 依赖：`npm install`
- 安装 Android Studio，并准备 Android SDK / JDK 17+
- 后端需要允许 Capacitor WebView 来源：`http://localhost`（默认配置和 `.env.example` 已包含）

## API 地址

网页端默认继续使用 `/api/v1`，由 Vite 或 Nginx 代理到后端。

安卓端不硬编码生产 API 地址；默认使用构建产物中的 `/api/v1`。打包到真实后端时，构建前设置 `VITE_API_BASE_URL`，或只给原生端设置 `VITE_NATIVE_API_BASE_URL`：

```powershell
$env:VITE_API_BASE_URL = 'https://your-domain.example/api/v1'
npm run android:sync
```

实时计时离线状态与待同步队列使用 WebView 的 `localStorage`，不需要额外原生插件。Capacitor Android 端写入本地记录的 `source` 为 `android`。

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
