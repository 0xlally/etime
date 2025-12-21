# etime
目前市面上可以见到limer，滴答清单等时间管理工具，但是他们要收费，并且缺少一些我想要的功能，另外一方面原因是我们总是说自己学一个东西学了几个月，但这段时间里花在其中的有效时间又有多少呢？另外多次不自律的行为提醒我，靠人的意志自己管理自己是不靠谱的，需要加上一些可见的限制，所以我决定开发一个用着舒服，且开源的时间管理工具。

## Docker 快速启动（PostgreSQL）

1. 准备环境：需要 Docker + Docker Compose。
2. 复制环境变量：在 `backend` 目录创建 `.env`，可基于 `.env.example`（默认已配置容器内的 Postgres）。
3. 启动：在项目根目录执行 `docker compose up -d --build`。
4. 迁移：执行 `docker compose run --rm backend alembic upgrade head`（首次或有新迁移时）。
5. 后端接口：`http://localhost:8001/api/v1`。
6. 前端：已包含前端容器，访问 `http://localhost:3000`（Vite dev server，`/api` 代理到 backend）。

说明：当前 Compose 提供 Postgres 与后端服务；前端可继续本地 `npm install && npm run dev -- --host --port 3000` 访问，或后续再增加前端容器/静态构建。
