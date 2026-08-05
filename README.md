# ETime

ETime 是一个可自托管的时间工作台，包含计时、计划、目标、复盘、通知和 Android 自律模式。

## 公网地址

- Web：<https://time.lally.top>
- 项目仓库：<https://github.com/0xlally/etime>
- Android 下载：<https://github.com/0xlally/etime/releases/latest>

## 服务器部署

服务器要求：Docker、Docker Compose 和 Git。

```bash
git clone https://github.com/0xlally/etime.git
cd etime
cp backend/.env.example backend/.env
```

编辑 `backend/.env` 和根目录 `.env`，至少配置随机的 `JWT_SECRET`、数据库连接和生产域名的 `BACKEND_CORS_ORIGINS`，然后执行：

```bash
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
docker compose ps
```

默认服务端口：

- 前端：`3000`
- 后端 API：`8001`
- API 路径：`/api/v1`

更新已有部署：

```bash
git pull --ff-only origin main
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
```

## Android 构建

Android 工程位于 `frontend/android`，需要 Node.js、JDK 17+、Android SDK 和 Gradle wrapper。

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL = 'https://time.lally.top/api/v1'
npm run android:sync
cd android
.\gradlew.bat assembleRelease
```

签名配置放在 `~/.android/etime-release-keystore.properties`。配置存在时会生成签名 APK，否则生成 unsigned APK。

Debug 构建：

```powershell
cd frontend
npm run android:build:debug
```

## 本地开发

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

```bash
cd frontend
npm install
npm run dev -- --host --port 3000
```

本地 Web 地址：<http://localhost:3000>
