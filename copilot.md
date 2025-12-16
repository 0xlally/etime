你是我的代码助手。这个项目是时间管理工具：计时、分类、统计、热力图、管理员、工作目标评估与提醒/惩罚记录。

技术栈约束：
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 style + Async（优先）或 Sync（也可，但要统一）
- Alembic 迁移
- Pydantic v2 + pydantic-settings 做配置
- 鉴权：JWT access/refresh；密码 hash 用 passlib[bcrypt]
- 统一返回格式：{"code":0,"msg":"ok","data":...}（或直接标准 JSON，但要统一）
- 时间统一用 UTC 存储，前端展示再转本地；用户时区字段可预留
- RBAC：user/admin，admin 才能访问 /admin/*
- 重要：每个 API 都要有类型注解、错误处理、单元测试示例（pytest）

业务模型：
- User、Category、Session（计时记录）
- WorkTarget（工作目标）、WorkEvaluation（评估结果）
- Notification（通知记录）、PunishmentEvent（惩罚事件记录）
- AdminAuditLog（管理员审计日志）
