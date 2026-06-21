# MySQL 连接失败问题修复指南（FIX_GUIDE）

## 问题现象

执行 `docker compose up` 后，backend 服务启动时报错：

```
Can't connect to MySQL server on 'db' (Connection refused)
```

虽然 db 容器状态显示为 `healthy`，但 backend 仍然无法连接到 MySQL。

---

## 根因分析

### 1. 健康检查使用 `localhost`（Socket 而非 TCP）

**问题**：原健康检查命令使用 `mysqladmin ping -h localhost`

```yaml
test: ["CMD", "mysqladmin", "ping", "-h", "localhost", ...]
```

`-h localhost` 在 MySQL 中默认走 **Unix Socket** 连接（`/var/run/mysqld/mysqld.sock`），而 backend 服务是通过 **TCP 连接**（`db:3306`）访问数据库的。

MySQL 启动时，Socket 文件可能比 TCP 端口更早就绪，导致健康检查已通过但 TCP 端口尚未监听，backend 连接时被拒绝。

**修复**：改用 `-h 127.0.0.1 -P 3306` 强制走 TCP 连接。

### 2. CMD 形式不展开环境变量

**问题**：使用 `["CMD", ...]` 数组形式（exec 形式）

```yaml
test: ["CMD", "mysqladmin", "ping", ..., "-p${MYSQL_ROOT_PASSWORD}"]
```

exec 形式不会通过 shell 执行，因此 `${MYSQL_ROOT_PASSWORD}` 不会被替换为实际值，导致健康检查命令始终失败（密码错误），或者即使 MySQL 实际正常也无法正确验证。

**修复**：改用 `["CMD-SHELL", "..."]` 形式，通过 shell 执行以正确展开环境变量。

### 3. 缺少 `start_period` 配置

**问题**：MySQL 首次启动时需要初始化数据目录、创建系统表、设置 root 密码等，这个过程可能需要 20-30 秒。

原配置没有 `start_period`，导致 MySQL 还在初始化阶段就开始计算重试次数，可能在服务真正就绪前就耗尽重试次数被标记为 unhealthy。

**修复**：添加 `start_period: 20s`，在启动初期的宽限期内不计入失败次数。

### 4. 缺少应用层重试机制

**问题**：backend 使用 `gunicorn --preload` 启动，会在 master 进程中立即加载 Flask 应用。如果此时数据库仍不可用（即使健康检查通过，也可能存在毫秒级的时序问题），应用会直接崩溃。

**修复**：在应用启动逻辑中添加数据库连接重试，最多重试 30 次，每次间隔 2 秒（最长约 60 秒）。

---

## 修复方案（三层防护）

### 第一层：优化 Docker 健康检查

修改 `docker-compose.yml` 中 db 服务的 healthcheck 配置：

```yaml
healthcheck:
  # 使用 CMD-SHELL 确保环境变量展开，使用 127.0.0.1 强制 TCP 连接
  test: ["CMD-SHELL", "mysql -h 127.0.0.1 -P 3306 -uroot -p${MYSQL_ROOT_PASSWORD:-123456} -e 'SELECT 1' >/dev/null 2>&1"]
  interval: 5s        # 检查间隔从 10s 缩短到 5s，更快感知就绪
  timeout: 3s         # 单次超时时间
  retries: 20         # 失败重试次数从 10 次增加到 20 次
  start_period: 20s   # 启动宽限期（首次启动 MySQL 初始化需要时间）
```

**关键改进点**：

| 项目 | 修改前 | 修改后 | 原因 |
|------|--------|--------|------|
| 连接方式 | `-h localhost`（Socket） | `-h 127.0.0.1 -P 3306`（TCP） | 与 backend 实际连接方式一致 |
| 验证方式 | `mysqladmin ping` | `mysql -e 'SELECT 1'` | 不仅验证进程存活，还验证查询能力 |
| 执行形式 | `CMD`（exec） | `CMD-SHELL`（shell） | 确保 `${MYSQL_ROOT_PASSWORD}` 被正确展开 |
| 检查间隔 | 10s | 5s | 更快感知服务就绪 |
| 重试次数 | 10 次 | 20 次 | 更长的等待窗口 |
| 启动宽限期 | 无 | 20s | 首启初始化不计入失败 |

### 第二层：depends_on + service_healthy 条件

**已有配置，无需修改**：

```yaml
backend:
  depends_on:
    db:
      condition: service_healthy
```

这确保 backend 容器**只有在 db 健康检查通过后才会启动**。

> 注意：`depends_on` 只控制启动顺序，无法保证应用层完全就绪，因此需要第三层防护。

### 第三层：应用层数据库连接重试

在 `backend/app/services/bootstrap_service.py` 中新增 `_wait_for_db()` 函数，在系统初始化前先等待数据库连接就绪：

```python
def _wait_for_db(app, max_retries: int = 30, retry_interval: int = 2) -> None:
    """
    等待数据库连接就绪，防止 Docker 环境下 MySQL 未完全启动导致启动失败。
    """
    with app.app_context():
        for attempt in range(1, max_retries + 1):
            try:
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                logger.info("数据库连接成功（第 %d 次尝试）", attempt)
                return
            except Exception as exc:
                logger.warning(
                    "数据库连接失败（第 %d/%d 次尝试）：%s，%d 秒后重试...",
                    attempt, max_retries, exc, retry_interval,
                )
                db.session.rollback()
                if attempt == max_retries:
                    logger.error("数据库连接重试次数已达上限，启动失败")
                    raise
                time.sleep(retry_interval)
```

并在 `initialize_defaults()` 函数开头调用：

```python
def initialize_defaults(app) -> None:
    _wait_for_db(app)    # 新增：等待数据库就绪
    with app.app_context():
        db.create_all()
        # ... 后续初始化逻辑
```

**重试策略**：
- 最大重试次数：30 次
- 每次间隔：2 秒
- 最长等待时间：约 60 秒
- 重试期间输出警告日志，便于排查问题

---

## 修改的文件清单

| 文件 | 修改内容 |
|------|---------|
| `docker-compose.yml` | 优化 db 服务 healthcheck 配置 |
| `backend/app/services/bootstrap_service.py` | 新增 `_wait_for_db()` 函数，在初始化前等待数据库 |

---

## 验证方法

### 1. 完全冷启动验证

```bash
# 清理所有数据和容器（首次启动场景）
docker compose down -v

# 重新构建并启动
docker compose up --build

# 观察 backend 日志，确认数据库连接重试正常工作
docker compose logs -f backend
```

预期结果：
- db 容器健康检查在 MySQL 完全就绪后才标记为 healthy
- backend 在 db 健康后启动，并成功连接数据库
- backend 日志中出现 "数据库连接成功（第 1 次尝试）"

### 2. 重启验证

```bash
# 重启所有服务
docker compose restart

# 检查服务状态
docker compose ps
```

预期结果：所有服务快速恢复正常，backend 无需重试或仅需 1-2 次重试即可连接。

### 3. 单独重启 db 验证

```bash
# 单独重启 db，观察 backend 是否能重连
docker compose restart db

# 检查 backend 健康状况
docker compose logs backend --tail 20
```

> 注意：应用层重试仅在**启动阶段**生效。运行时数据库断开需要额外的连接池配置（如 `pool_pre_ping`），不在本次修复范围内。

---

## 可选进一步优化

### 1. SQLAlchemy 连接池保活

在 `config.py` 中添加连接池配置，防止运行时连接断开：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,      # 每次取出连接前先验证
    "pool_recycle": 3600,       # 连接最大存活时间（秒）
    "pool_size": 10,            # 连接池大小
    "max_overflow": 20,         # 最大溢出连接数
}
```

### 2. backend 服务也添加健康检查

确保 backend 真正可用后再对外提供服务：

```yaml
backend:
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
    interval: 10s
    timeout: 3s
    retries: 3
    start_period: 30s
```

### 3. 使用 `wait-for-it` 脚本

在 backend 容器入口处使用 wait-for-it 脚本等待数据库端口：

```bash
# 下载 wait-for-it.sh 到 backend 目录
# 修改 Dockerfile，在 CMD 前先执行等待
CMD ["./wait-for-it.sh", "db:3306", "--", "gunicorn", ...]
```

本次修复采用了"健康检查 + 应用层重试"的组合方案，已能覆盖绝大多数场景，可选优化按需启用。
