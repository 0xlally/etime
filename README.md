# ETime

自托管的时间管理、目标跟踪与复盘工具。ETime 把实时计时、手动补录、计划日历、目标引擎、复盘统计、热力预览、复盘海报和小组协作放在一个简约的个人时间工作台里，适合学习、工作、备考和长期习惯管理。

线上体验：<http://time.lally.top>

## 为什么做它

很多时间记录工具只回答“我花了多久”，ETime 更想回答三个问题：

- 今天开始起来够不够轻？
- 这段时间有没有真的靠近目标？
- 复盘时能不能一眼看到节奏，而不是重新翻账？

所以它不是单纯秒表，也不是厚重项目管理系统，而是一个可以长期自托管的时间系统。

## 视觉与交互

ETime 当前采用简约黑白线条风：页面以白底、黑字、黑色边线为主，去掉淡黄色、大面积色块和装饰阴影，让计时、计划、目标和复盘数据更像一张清爽的工作台。分类色点、快捷卡片色标、热力块和时痕绿色时间线保留原有颜色，因为它们承担数据识别作用。

计时页按真实使用顺序重新整理：先选择分类，再看大号计时器和开始按钮，常用卡片放在下方作为快捷入口；补录独立成同一张主卡里的模式，不再重复出现多套分类入口。计划页简化为“计划”，保留新增事项、月/周/日视图、待安排池和目标节奏，月视图优先浏览安排，周/日视图承载更完整的任务操作。

桌面端采用左侧导航栏和宽工作区布局，适合长时间浏览计划、目标和复盘；手机/Android 端采用顶部应用栏加底部 Tab 导航，通知按钮和退出按钮使用稳定的圆形图标按钮。通知下拉支持点外部关闭，并会在切换页面时自动收起，避免遮挡后续操作。

## 界面预览

![目标与分类卡片](frontend/public/project/0245b0a6ecc0c31d16f9d4c770fa7523.png)

![计时器与模式切换](frontend/public/project/3d9f947c5ed5aa711ea7fbdcbae5d40b.png)

![复盘统计与热力预览](frontend/public/project/9a11cfbfea346c5d542d072a8da6c516.png)

> 推广素材建议重新截新版黑白线条风界面，优先补 3 张：`/review` 复盘聚合页、`/planner` 计划日历、`/share` 复盘海报。

## 核心功能

- 计时工作台：分类优先的实时计时、快捷开始模板、手动补录、离线启动/停止、刷新恢复、联网自动同步。
- 快捷开始：把“阅读 25 分钟”“英语 30 分钟”等高频事项做成卡片，一点就开始。
- 复盘聚合：日报/周报集中呈现分类占比、历史趋势、目标达成、时痕和近 8 周热力预览，减少统计与热力图的重复入口。
- 目标引擎：支持日/周/月/明天目标，包含进度、连胜、完成率、时间债务和补偿记录。
- 计划日历：月/周/日视图、待安排池、事项提醒、完成后转时间记录；月视图简洁浏览，周/日视图承载快捷操作。
- 自动复盘：支持按日期查看日报/周报，点击热力格可直接切换到对应日复盘，并支持导出 Markdown。
- 分享海报：生成今日/本周/本月复盘卡片，支持隐私模式和 PNG 导出。
- 小组协作：邀请码加入小组、轻量群聊、成员列表、分享今日状态和复盘卡片摘要。
- 账号安全：JWT 登录、刷新令牌、邮箱找回密码；重置令牌绑定当前密码状态，改密后自动失效。
- Android 端：基于 Capacitor 复用 Web 前端，支持生产 API 打包和本地离线计时队列。

## 技术栈

- 前端：React 18、Vite、TypeScript、Tailwind CSS、Recharts、lucide-react
- 后端：FastAPI、SQLAlchemy、Alembic、PostgreSQL
- 移动端：Capacitor Android
- 部署：Docker Compose、Nginx、PostgreSQL
- 认证与安全：JWT、SMTP 密码重置、登录/重置限流、Android PBKDF2 自律模式密码

## 快速开始

### 本地开发

```bash
cd backend
pip install -r requirements.txt
pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

```bash
cd frontend
npm install
npm run dev -- --host --port 3000
```

开发入口：

- Web: <http://localhost:3000>
- API: <http://localhost:8001/api/v1>
- API 文档: <http://localhost:8001/api/v1/docs>

### Docker Compose

在仓库根目录创建 `.env`：

```env
POSTGRES_DB=etime
POSTGRES_USER=etime
POSTGRES_PASSWORD=replace-with-a-long-random-password
```

复制并配置后端环境：

```bash
cp backend/.env.example backend/.env
```

启动：

```bash
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
```

默认端口：

- 前端容器：`http://localhost:3000`
- 后端 API：`http://localhost:8001/api/v1`

## 关键配置

生产环境至少检查这些变量：

- `JWT_SECRET`：必须换成长随机值。
- `DATABASE_URL`：Docker Compose 默认由根目录 `.env` 注入 PostgreSQL 地址。
- `BACKEND_CORS_ORIGINS`：按实际域名配置。
- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM`：启用找回密码邮件。
- `AUTO_INIT_ADMIN=False`：默认不自动创建管理员；确需种子管理员时，`DEFAULT_ADMIN_PASSWORD` 至少 12 位且不能使用常见默认密码。

## Android

Android 工程位于 `frontend/android`。

调试包：

```powershell
cd frontend
npm run android:sync
npm run android:build:debug
```

生产 API 打包：

```powershell
cd frontend
$env:VITE_API_BASE_URL = 'https://your-domain.example/api/v1'
npm run android:sync
cd android
.\gradlew.bat assembleRelease
```

未配置签名时，Gradle 只会产出 `app-release-unsigned.apk`。正式发布 GitHub Release 或应用市场前，请配置 release keystore 并生成签名 APK/AAB。

## 安全默认值

- 不内置可登录的默认管理员。
- Docker Compose 要求显式设置数据库密码，不默认暴露 PostgreSQL 到宿主机。
- 后端启动日志会脱敏数据库连接串，避免把密码写进日志。
- Docker 镜像不复制 `backend/.env`，敏感配置通过运行时环境变量注入。
- Android 禁止应用备份和明文 HTTP 流量。
- 自律模式本地密码使用 PBKDF2-HMAC-SHA256 派生存储。
- 前端运行时依赖已通过 `npm audit --omit=dev` 检查。

## API 概览

主要接口都挂在 `/api/v1` 下：

- `POST /auth/register`、`POST /auth/login`、`POST /auth/refresh`
- `GET /users/me`
- `GET|POST /categories`
- `POST /sessions/start`、`POST /sessions/stop`、`POST /sessions/manual`
- `GET /stats/summary`
- `GET /heatmap`
- `GET|POST /targets`、`GET /targets/dashboard`
- `GET /reviews/daily`、`GET /reviews/weekly`
- `GET /share/summary?range=today|week|month`
- `GET|POST /calendar-tasks`
- `GET|POST /quick-start-templates`
- `GET|POST /groups`

## 验证

本轮体验调整已执行：

- `cd frontend && npm run build`
- `cd frontend && $env:VITE_NATIVE_API_BASE_URL='http://127.0.0.1:8001/api/v1'; npm run android:sync`
- `cd frontend/android && .\gradlew.bat assembleDebug`
- Web 端使用桌面、平板和手机宽度截图检查 `/timer`、`/planner`、`/review`、`/share`、`/groups`，未发现非预期横向溢出。
- Android 真机已安装调试包并截图检查 `/timer`、通知下拉和 `/planner`；右上角通知/退出图标居中，通知下拉切换页面后会自动关闭。

Android 真机安装需要手机端确认安装权限；若系统拒绝安装，请先解锁手机并允许 USB 安装后重新执行 `adb install -r frontend/android/app/build/outputs/apk/debug/app-debug.apk`。

## 推广文案

博客风项目介绍见 [docs/project-introduction.md](docs/project-introduction.md)。
