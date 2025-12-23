# etime
目前市面上可以见到limer，滴答清单等时间管理工具，但是他们要收费，并且缺少一些我想要的功能，另外一方面原因是我们总是说自己学一个东西学了几个月，但这段时间里花在其中的有效时间又有多少呢？另外多次不自律的行为提醒我，靠人的意志自己管理自己是不靠谱的，需要加上一些可见的限制，所以我决定开发一个用着舒服，且开源的时间管理工具。

## Docker 部署指南（PostgreSQL）

1) 依赖准备
- Docker 与 Docker Compose。
- 可选：本机访问容器内 Postgres 使用 55432 端口映射。

2) 环境变量
- 在 backend 目录创建 `.env`（可复制 `.env.example`）。默认数据库连接指向 Compose 内的 Postgres 服务 `db`。
- 如需覆盖前端 API 代理目标，设置 `API_PROXY_TARGET`（默认 http://backend:8001）。

3) 启动与构建
- 在项目根目录执行 `docker compose up -d --build`。
- 首次或有新迁移时，运行 `docker compose run --rm backend alembic upgrade head`。

4) 数据迁移（如需从本地 SQLite 导入）
- 放置源库 backend/app.db。
- 运行 `docker compose run --rm backend python migrate_sqlite_to_pg.py --sqlite sqlite:///./app.db --pg postgresql+psycopg2://etime:etime_pass@db:5432/etime`。

5) 访问入口
- 后端 API: http://localhost:8001/api/v1
- 前端: http://localhost:3000 （Vite dev server 已代理 `/api` 到 backend）

6) 常用运维
- 重启服务：`docker compose restart backend frontend`。
- 查看数据库：`docker exec -it etime_db psql -U etime -d etime`（或通过 host 连接 `localhost:55432`）。

说明：Compose 已包含前后端与 Postgres。若需本地开发前端，可在 frontend 目录执行 `npm install && npm run dev -- --host --port 3000` 并继续使用 `/api` 代理。

## 本地开发与测试

- 本地运行后端用例（使用临时 SQLite）：`cd backend && DATABASE_URL=sqlite:///./test.db pytest`
- 该命令会在 backend 目录生成临时 SQLite 数据库文件，属于本地工件，可随时清理。
- 避免将本地生成的数据库文件或测试缓存提交到仓库，保持工作区干净。
