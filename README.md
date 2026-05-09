# ETime

ETime 是一个开源、自托管的时间工作台，把计时、补录、计划、目标、复盘、分享海报、小组协作和 Android 自律模式放在同一套安静清晰的系统里。

它不是只回答“我花了多久”的秒表，而是帮你持续回答三个问题：

- 今天的投入够不够，离目标还差多少？
- 哪些分类、任务和习惯正在真正推进长期目标？
- 复盘时能不能一眼看到节奏，而不是重新翻账？

在线体验：<http://time.lally.top>

项目地址：<https://github.com/0xlally/etime>

## 界面预览

### 计时工作台

常用卡片、今日剩余、分类选择和大号计时器放在同一个首屏里。高频事项一键开始，临时事项也可以直接选分类计时。

![ETime 计时工作台](docs/assets/screenshots/timer-home.png)

### 计划与目标

月、周、日三种视图管理任务；待安排池先收纳想法，再安排到具体时间。目标进度和计划在同一页里联动，避免“计划归计划、目标归目标”。

![ETime 计划页面](docs/assets/screenshots/planner.png)

### 复盘与热力

日报、周报、月报聚合分类占比、目标达成、趋势、时痕和近 8 周热力，支持导出 Markdown。

![ETime 复盘页面](docs/assets/screenshots/review.png)

### 复盘海报

把今天、本周或本月的投入生成一张适合保存和分享的卡片，支持隐私模式、不同样式和 PNG 导出。

![ETime 复盘海报](docs/assets/screenshots/share-card.png)

### 小组协作

用邀请码加入轻量小组，分享今日状态、复盘卡片和文字消息，适合自习、备考、写作和项目结伴。

![ETime 小组协作](docs/assets/screenshots/groups.png)

### Android 体验

Android 端复用同一套前端体验，加入离线计时队列和自律模式。自律模式可统计今日手机使用时长，超过上限后通过悬浮提醒介入。

![ETime Android 计时](docs/assets/screenshots/mobile-timer.png)

![ETime Android 自律模式](docs/assets/screenshots/android-discipline.png)

## 核心功能

### 1. 计时与补录

- 实时计时：选择分类后开始，结束时自动生成 session。
- 快捷卡片：把“英语 30 分钟”“阅读 25 分钟”等高频事项做成一键入口。
- 固定时长提醒：模板到点后提醒继续或结束。
- 手动补录：忘记开计时时，可以补录日期、分类、小时、分钟和备注。
- 效率系数：结束时可用系数折算有效时长。
- 离线恢复：断网、刷新或 Android 前台切换后，本地运行状态仍可恢复并等待同步。

### 2. 目标引擎

- 支持每日、每周、每月、明日目标。
- 可限定统计某些分类，适合学习、健身、写作、备考等长期投入。
- 展示当前进度、剩余时长、连续达成、最佳连续、完成率、时间债务和补偿建议。
- 目标进度会出现在计时首页、计划页、通知和复盘里。

### 3. 计划日历

- 月视图用于浏览安排，周/日视图用于更密集的任务操作。
- 待安排池收纳还没有具体时间的任务。
- 支持优先级、预计时长、提醒、完成、取消、转成时间记录和从计划直接开始计时。
- 适合把“想做的事”落到具体时间块里。

### 4. 复盘、统计与热力

- 日报、周报、月报覆盖总时长、分类趋势、目标达成和时间轨迹。
- 近 8 周热力图帮助判断节奏是否稳定。
- 支持 Markdown 导出，方便沉淀到博客、Notion、Obsidian 或周报。
- 时间轨迹记录一天中的关键状态，让数字和上下文一起保留。

### 5. 分享海报

- 支持今日、本周、本月三种范围。
- 提供简洁、数据感、热力图三种卡片样式。
- 隐私模式可隐藏真实分类名和具体时长。
- Web 端可导出 PNG，Android 端可调用系统分享。

### 6. 小组协作

- 创建/加入小组，使用邀请码轻量协作。
- 支持公开小组申请、成员列表、群聊消息。
- 支持分享今日状态和复盘卡片摘要。
- 适合自习小组、学习搭子、备考打卡群、写作/开发结伴。

### 7. Android 自律模式

- Capacitor Android 客户端复用 Web 功能。
- 原生侧统计今日手机使用时长。
- 可设置每日上限、统计全部应用或指定应用。
- 使用 Android 使用情况访问和悬浮窗权限，超过上限后显示悬浮提醒。
- 本地解锁密码使用 PBKDF2-HMAC-SHA256 派生存储。

### 8. 账号、安全与部署

- JWT access token + refresh token 登录。
- 邮箱找回密码，重置令牌绑定当前密码状态，改密后自动失效。
- 管理端支持用户、session 和审计日志管理。
- Docker Compose 自托管，默认不内置可登录管理员。
- Android 禁止应用备份，生产构建可指定真实 API 地址。

## 技术栈

- 前端：React 18、Vite、TypeScript、Tailwind CSS、Recharts、lucide-react
- 后端：FastAPI、SQLAlchemy、Alembic、PostgreSQL
- 移动端：Capacitor Android、原生自律模式插件
- 部署：Docker Compose、Nginx、PostgreSQL
- 认证与安全：JWT、SMTP 密码重置、PBKDF2 本地密码派生

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

- 前端容器：<http://localhost:3000>
- 后端 API：<http://localhost:8001/api/v1>

## 关键配置

生产环境至少检查：

- `JWT_SECRET`：必须替换为长随机值。
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

如已在 `~/.android/etime-release-keystore.properties` 配置 release keystore，Gradle 会生成签名 release APK；否则会生成 unsigned APK，需要签名后再分发。

## API 概览

主要接口挂在 `/api/v1` 下：

- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- `GET /users/me`
- `GET|POST /categories`
- `POST /sessions/start`, `POST /sessions/stop`, `POST /sessions/manual`
- `GET /stats/summary`
- `GET /heatmap`
- `GET|POST /targets`, `GET /targets/dashboard`
- `GET /reviews/daily`, `GET /reviews/weekly`, `GET /reviews/monthly`
- `GET /share/summary?range=today|week|month`
- `GET|POST /calendar-tasks`
- `GET|POST /quick-start-templates`
- `GET|POST /groups`

## 验证

本次发布前已执行：

- `cd frontend && npm run build`
- `cd frontend && npm run android:sync`
- `cd frontend/android && .\gradlew.bat assembleRelease`
- 使用 Playwright 在桌面和手机宽度生成并检查文档截图。

## 推广文案

完整项目介绍见 [docs/project-introduction.md](docs/project-introduction.md)。

一句话版本：

> ETime 是一个开源、自托管的时间工作台：计时、计划、目标、复盘、分享和小组协作，都放在一套安静清晰的系统里。
