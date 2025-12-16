# FastAPI 开发文档

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理 (pydantic-settings)
│   │   └── db.py              # 数据库连接和会话
│   └── api/
│       ├── __init__.py
│       ├── router.py          # 路由聚合
│       ├── deps.py            # 依赖函数 (get_db, get_current_user 等)
│       └── endpoints/
│           ├── __init__.py
│           └── health.py      # 健康检查端点
├── alembic/
│   ├── env.py                 # Alembic 环境配置
│   ├── script.py.mako         # 迁移文件模板
│   └── versions/              # 数据库迁移文件目录
├── alembic.ini                # Alembic 配置文件
├── pyproject.toml             # 项目配置和依赖 (推荐)
├── requirements.txt           # Python 依赖列表
├── .env.example               # 环境变量示例
└── README_DEV.md              # 本文件
```

## 快速开始

### 1. 环境准备

确保已安装 Python 3.10 或更高版本：

```bash
python --version
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 使用 pip
cd backend
pip install -r requirements.txt

# 或使用 pyproject.toml (推荐)
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 如果使用 PostgreSQL
pip install -e ".[postgres]"

# 如果使用 MySQL
pip install -e ".[mysql]"
```

### 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，修改配置
# 重点修改：
# - DATABASE_URL: 数据库连接字符串
# - JWT_SECRET: JWT 密钥（生产环境必须修改）
```

### 5. 运行应用

```bash
# 从 backend 目录运行
uvicorn app.main:app --reload

# 指定端口
uvicorn app.main:app --reload --port 8000

# 指定 host (允许外部访问)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

应用将在 http://localhost:8000 启动

### 6. 访问 API 文档

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

### 7. 测试健康检查

```bash
# 使用 curl
curl http://localhost:8000/api/v1/health

# 使用浏览器访问
http://localhost:8000/api/v1/health
```

## 数据库迁移 (Alembic)

### Alembic 初始化

项目已经配置好 Alembic，无需重新初始化。如果需要重新初始化：

```bash
# 删除 alembic 目录和 alembic.ini
# 然后运行
alembic init alembic
```

### 创建第一个迁移

在创建迁移之前，确保已经定义了数据库模型。

1. **创建模型文件** (示例):

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
```

2. **在 alembic/env.py 中导入模型**:

```python
# 在 alembic/env.py 中添加
from app.models.user import User  # 导入所有模型
```

### Alembic 常用命令

#### 自动生成迁移文件

```bash
# 自动检测模型变化并生成迁移
alembic revision --autogenerate -m "Initial migration"

# 示例消息
alembic revision --autogenerate -m "Add users table"
alembic revision --autogenerate -m "Add email verification field"
```

#### 手动创建迁移文件

```bash
# 创建空白迁移文件
alembic revision -m "migration message"
```

#### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级指定步数
alembic upgrade +1
alembic upgrade +2

# 升级到指定版本
alembic upgrade <revision_id>
```

#### 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚到初始状态
alembic downgrade base
```

#### 查看迁移历史

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 详细历史
alembic history --verbose
```

#### 查看 SQL 而不执行

```bash
# 查看升级 SQL
alembic upgrade head --sql

# 查看降级 SQL
alembic downgrade -1 --sql
```

### Alembic 工作流程示例

```bash
# 1. 修改或创建模型文件
# app/models/user.py

# 2. 确保模型在 alembic/env.py 中被导入

# 3. 生成迁移文件
alembic revision --autogenerate -m "Add users table"

# 4. 检查生成的迁移文件
# 查看 alembic/versions/ 目录下的新文件

# 5. 执行迁移
alembic upgrade head

# 6. 验证迁移
# 检查数据库表是否正确创建
```

### 数据库连接配置

在 `.env` 文件中配置不同的数据库：

```bash
# SQLite (默认，适合开发)
DATABASE_URL=sqlite:///./app.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname
```

## 开发指南

### 添加新的 API 端点

1. **创建端点文件**:

```python
# app/api/endpoints/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return {"users": []}
```

2. **在路由中注册**:

```python
# app/api/router.py
from .endpoints import users

api_router.include_router(users.router, prefix="/users", tags=["users"])
```

### 使用依赖函数

```python
from fastapi import Depends
from app.api.deps import get_db, get_current_user

@router.get("/protected")
def protected_route(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return {"user": current_user}
```

### 环境变量配置

在 [app/core/config.py](app/core/config.py) 中添加新的配置项：

```python
class Settings(BaseSettings):
    NEW_CONFIG: str = "default_value"
```

在 `.env` 文件中设置：

```bash
NEW_CONFIG=my_value
```

## 生产部署建议

### 1. 修改配置

```bash
# .env
DEBUG=False
JWT_SECRET=<使用强随机密钥>
DATABASE_URL=<生产数据库连接>
```

### 2. 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 运行
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. 使用 Docker (可选)

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 常见问题

### Q: 如何重置数据库？

```bash
# 删除数据库文件 (SQLite)
rm app.db

# 重新运行迁移
alembic upgrade head
```

### Q: 迁移失败怎么办？

```bash
# 1. 检查当前版本
alembic current

# 2. 回滚到上一个版本
alembic downgrade -1

# 3. 修复迁移文件后重新执行
alembic upgrade head
```

### Q: 如何查看数据库表结构？

使用数据库客户端工具：
- SQLite: DB Browser for SQLite
- PostgreSQL: pgAdmin, DBeaver
- MySQL: MySQL Workbench, DBeaver

## 下一步

1. 实现用户认证系统 (JWT)
2. 添加更多业务端点
3. 编写单元测试和集成测试
4. 配置 CI/CD 流程
5. 添加日志系统
6. 实现缓存机制 (Redis)

## 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
