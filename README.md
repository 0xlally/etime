# ETime – 开源时间管理与目标跟踪

一个自托管的时间管理/目标跟踪工具，支持实时计时、手动补录、分类统计、目标进度提醒，前后端开源可自由部署。线上演示与自用地址：<http://time.lally.top>。

## 功能亮点
- 计时模式：实时计时、快捷开始模板与手动补录，支持系数折算与取整；实时计时支持离线启动/停止、刷新恢复和联网后自动同步。
- 快捷开始：可创建“英语 30 分钟”“阅读 25 分钟”等常用计时卡片，点击后自动选择分类并开始计时，固定时长到点会前台提醒继续或结束。
- 目标进度：按日/周/月（含“明天”）显示目标窗口、剩余时长、已完成时长。
- 目标引擎 2.0：支持连胜、最佳连胜、完成率、时间债务、补偿记录和惩罚/奖励可视化。
- 自动复盘：日报/周报串联统计、目标达成、分类趋势和时痕，并支持一键导出 Markdown。
- 小组协作 MVP：支持创建/加入/退出学习小组、邀请码邀请、成员列表、轻量群聊、分享今日状态和复盘卡片摘要。
- 分类管理：分类选择与新建一体化卡片，对齐控件减少跳跃感。
- 统计视图：分类占比、热力图、目标达成等多视角复盘（前端已内置对应页面）。
- 账号安全：JWT 登录、刷新令牌、邮箱密码重置；重置令牌会绑定当前密码状态，使用一次后自动失效。
- 安卓端：通过 Capacitor 复用现有前端，支持同步 Web 构建产物并生成 debug APK。
- 开箱即用：Docker Compose 一键拉起前后端与 PostgreSQL。

## 技术栈
- 前端：React + Vite + TypeScript + Tailwind + Recharts
- 后端：FastAPI + SQLAlchemy + Alembic + PostgreSQL
- 其他：JWT 认证、SMTP 邮件、Docker Compose、Nginx（前端容器）、Capacitor Android

## 在线体验
- 公网地址：<http://time.lally.top>

## 界面预览

![目标与分类卡片](frontend/public/project/0245b0a6ecc0c31d16f9d4c770fa7523.png)
![计时器与模式切换](frontend/public/project/3d9f947c5ed5aa711ea7fbdcbae5d40b.png)
![统计与热力图](frontend/public/project/9a11cfbfea346c5d542d072a8da6c516.png)

## 部署（Docker Compose）

1) 依赖
- Docker、Docker Compose
- 可选：本机访问容器内 Postgres 可用 55432:5432 映射

2) 环境变量
- 在仓库根目录创建 `.env`，至少设置一个强随机数据库密码：

```env
POSTGRES_DB=etime
POSTGRES_USER=etime
POSTGRES_PASSWORD=replace-with-a-long-random-password
```

- backend 目录创建 `.env`（可复制 `.env.example`）
- 默认数据库指向 Compose 内的 `db`；如需前端改代理，设置 `API_PROXY_TARGET`（默认 `http://backend:8001`）
- 已完全使用 PostgreSQL，部署不需要也不会生成 SQLite 文件。
- 找回密码邮件需要配置 `SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD` 等 SMTP 变量；未配置时接口仍返回通用提示，但后台日志会记录发送失败。
- 登录和找回密码默认启用轻量限流，可通过 `LOGIN_RATE_LIMIT_*` 和 `PASSWORD_RESET_RATE_LIMIT_*` 调整。
- 默认不会自动创建管理员账号。若确需本地种子管理员，必须显式设置 `AUTO_INIT_ADMIN=True` 和至少 12 位、非默认值的 `DEFAULT_ADMIN_PASSWORD`。

3) 启动
- `docker compose up -d --build`
- 首次或迁移变更：`docker compose run --rm backend alembic upgrade head`


4) 访问
- 后端 API: `http://localhost:8001/api/v1`
- 前端: `http://localhost:3000`（开发模式 Vite 代理 `/api` 到 backend）

5) 常用运维
- 重启：`docker compose restart backend frontend`
- 查库：`docker exec -it etime_db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"`
- PostgreSQL 默认只在 Compose 内网可用，不再映射到宿主机。需要临时直连时可手动添加本地端口映射，不建议生产环境暴露。

## 小组协作 MVP

小组页面位于 `/groups`，导航栏入口为“小组”。第一版 intentionally 保持轻量：

- 创建小组后自动成为 owner，并生成 10 位邀请码。
- 成员可通过邀请码加入小组，非成员无法读取成员列表或消息。
- 小组内支持文本消息、系统提示、今日状态分享和复盘卡片摘要分享。
- 今日状态会聚合当前用户当天总时长、Top 分类、目标完成数和简单连续记录天数。
- Web 端使用 7 秒轮询刷新当前小组消息；页面离开时会自动停止轮询。
- 移动端/Capacitor Android 使用聊天式布局：顶部小组信息、中间消息滚动、底部输入区固定。

后端 API：

- `GET /api/v1/groups`
- `POST /api/v1/groups`
- `GET /api/v1/groups/{group_id}`
- `PATCH /api/v1/groups/{group_id}`
- `POST /api/v1/groups/join`
- `POST /api/v1/groups/{group_id}/leave`
- `GET /api/v1/groups/{group_id}/members`
- `GET /api/v1/groups/{group_id}/messages?before=&limit=50`
- `POST /api/v1/groups/{group_id}/messages`
- `POST /api/v1/groups/{group_id}/share-status`
- `POST /api/v1/groups/{group_id}/share-card`

权限约束：

- 只有小组成员能读取小组、成员列表和消息，也只有成员能发消息或分享状态。
- owner/admin 可修改小组信息。
- MVP 阶段 owner 不能直接退出小组。
- 文本消息限制为 1000 字以内。

## 快捷开始模板

计时器页面顶部提供“快捷开始”区域，适合高频任务：

- 模板字段包括标题、分类、固定时长、备注模板、排序、颜色、图标和启用状态。
- 点击模板卡片会自动选择对应分类并开始实时计时；若已有 active session，后端返回 409，前端会提示先停止当前计时。
- 固定时长模板会展示剩余倒计时；到点后在 Web 和 Capacitor Android 前台弹窗询问“继续计时”或“结束”。
- 模板管理支持新建、编辑、删除，以及简单上移/下移排序。
- 快捷开始复用现有离线计时 localStorage 队列；模板启动会携带 `client_generated_id`，联网重试时可幂等恢复同一条 session。

后端 API：

- `GET /api/v1/quick-start-templates`
- `POST /api/v1/quick-start-templates`
- `PATCH /api/v1/quick-start-templates/{template_id}`
- `DELETE /api/v1/quick-start-templates/{template_id}`
- `POST /api/v1/quick-start-templates/{template_id}/start`

数据库迁移：

- 新增 Alembic migration：`20260506_add_quick_start_templates`
- 升级命令：`cd backend && alembic upgrade head`

## 安全默认值

- 不内置可登录的默认管理员；`admin/admin123` 不会被自动创建。
- `docker-compose.yml` 不再使用默认数据库密码，也不默认暴露 PostgreSQL 端口。
- 前端退出登录会同时清理 access token 和 refresh token。
- Android Manifest 禁止应用备份和明文 HTTP 流量；自律模式密码使用 PBKDF2-HMAC-SHA256 派生存储。
- 运行时前端依赖已通过 `npm audit --omit=dev` 校验为 0 漏洞。

## 本地开发
- 前端：`cd frontend && npm install && npm run dev -- --host --port 3000`
- 后端用例：`cd backend && pytest`（默认使用 env 中的 PostgreSQL；如需隔离，可自行设置临时数据库连接）
- 保持工作区干净，避免提交本地生成的数据库文件或测试缓存。

## 安卓端

安卓端工程位于 `frontend/android`，使用 Capacitor 复用 `frontend/dist`。

常用命令：
- 同步 Web 构建产物到 Android：`cd frontend && npm run android:sync`
- 打开 Android Studio：`cd frontend && npm run android:open`
- 构建 debug APK：`cd frontend && npm run android:build:debug`

默认情况下，浏览器端和安卓端都使用构建产物中的 `/api/v1`。安卓端没有硬编码生产域名；打包到真实后端时，构建前显式设置 `VITE_API_BASE_URL` 或 `VITE_NATIVE_API_BASE_URL`：

```powershell
$env:VITE_API_BASE_URL = 'https://your-domain.example/api/v1'
npm run android:sync
```

实时计时的离线记录会保存在本地，包含 `local_timer_id`、分类、开始/结束时间、状态和来源（Web 为 `web`，Capacitor Android 为 `android`）。应用启动、进入计时页和浏览器/ WebView 恢复在线时都会尝试同步；后端使用 `client_generated_id` 做幂等去重，重复提交同一条本地记录不会创建重复 session。快捷开始模板会额外保存模板 ID、固定时长和到点提醒状态，Android 前台与 Web 一样弹出到点提醒；后续接入 Capacitor Local Notifications 时可复用这组本地字段。

小组功能 Android 手动验证建议：

1. 设置真实后端地址后运行 `cd frontend && npm run android:sync`。
2. 安装或打开 debug APK，登录账号，进入底部导航“小组”。
3. 创建小组，确认页面显示邀请码、成员数和消息空状态。
4. 发送一条文本消息，确认消息立即刷新且不重复追加。
5. 点击“分享今日状态”和“分享复盘卡片”，确认出现状态卡片和卡片摘要。
6. 用第二个账号通过邀请码加入，确认成员列表增加且非成员无法访问消息。
7. 切换到其他页面或退出小组页面，确认返回后消息仍能加载，轮询不会在后台持续刷新。

debug APK 输出位置：

```text
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

## 分享卡片 / 复盘海报

- 页面入口：`/share`，导航栏显示“分享”。
- 后端接口：`GET /api/v1/share/summary?range=today|week|month`。
- 分享卡片聚合当前登录用户的总时长、分类占比、目标完成状态、连续记录天数和热力图预览，不返回备注。
- 隐私模式会把分类名替换为“分类 A / 分类 B”，并可隐藏总时长。
- Web 端使用 `html-to-image` 生成并下载 PNG；Capacitor Android 前台使用同一套生成能力，若系统支持 Web Share 会尝试分享，否则降级为下载/长按保存。

## 计划日历 / 待安排事项

- 页面入口：`/planner`，`/calendar` 会重定向到 `/planner`。
- 页面包含月/周/日视图、待安排池、新增/编辑事项弹窗、今日计划摘要和前台提醒。
- 事项支持先进入待安排池，也可以安排到具体日期与时间段；已安排事项可完成、取消、开始计时或转成时间记录。
- “开始计时”会检查当前 active session，然后跳转到 Timer 并携带分类和 note 自动开始。
- Web 端使用 Notification API；无权限或 Android 前台场景使用站内提醒。后续若接入 Capacitor Local Notifications，可复用现有提醒字段。

后端 API：

- `GET /api/v1/calendar-tasks`
- `POST /api/v1/calendar-tasks`
- `PATCH /api/v1/calendar-tasks/{id}`
- `DELETE /api/v1/calendar-tasks/{id}`
- `POST /api/v1/calendar-tasks/{id}/complete?create_session=true|false`
- `GET /api/v1/calendar-tasks/reminders/due`
- `POST /api/v1/calendar-tasks/{id}/reminder-fired`

数据库迁移：

- `20260506_add_calendar_tasks`
- 升级命令：`cd backend && alembic upgrade head`
