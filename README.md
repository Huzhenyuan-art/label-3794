# 综合业务主网站（Main Portal）

## 🛠 技术栈（含选型理由）

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 前端框架 | **React 18** | 生态成熟、组件化开发效率高，与 Ant Design 深度集成，适合后台管理类项目 |
| UI 组件库 | **Ant Design 5** | 企业级开箱即用组件（表格/表单/弹窗/上传），中文友好，减少 UI 开发量 |
| 构建工具 | **Vite** | 基于 ESM 的极速冷启动与热更新，开发体验远优于 Webpack |
| HTTP 客户端 | **Axios** | 拦截器机制天然适配 JWT/CSRF Token 自动注入 |
| 后端框架 | **Flask 3 (Python 3.11)** | 轻量灵活、插件丰富，适合中小规模 API 服务；代码结构清晰、注释方便 |
| ORM | **SQLAlchemy** | Python 生态最成熟的 ORM，支持 Core 表达式防注入，兼顾灵活与安全 |
| 参数校验 | **Pydantic** | 声明式数据校验，自动生成友好错误信息，减少手写校验代码 |
| 认证鉴权 | **Flask-JWT-Extended** | 成熟的 JWT 方案，内置 Token 刷新/黑名单/Claims 注入 |
| 密码哈希 | **bcrypt** | 自适应哈希算法，防彩虹表/暴力破解，业界推荐的密码存储方案 |
| 数据库 | **MySQL 8.0**（兼容 5.0+） | 关系型数据库首选，表前缀/动态表方案成熟，社区资源丰富 |
| 容器化 | **Docker + Docker Compose** | 一键启动前端+后端+数据库，消除环境差异，简化部署流程 |
| 生产部署 | **Gunicorn + Nginx** | Gunicorn 多 Worker 并发处理 Python 请求；Nginx 做静态资源托管与反向代理 |

## 🚀 启动指南 (How to Run)
1. 确保 Docker Desktop 已启动。
2. 在项目根目录执行：`docker compose up --build`
3. 首次启动会自动完成数据库初始化、默认管理员账号创建、示例业务页面 Seed。

## 🔗 服务地址 (Services)
- Frontend 主站/后台: http://localhost:3000
- Backend API: http://localhost:8000
- Backend 健康检查: http://localhost:8000/health
- MySQL: localhost:3306 (user: root / pass: 123456 / db: label_portal)

## 🧪 测试账号
- Admin: `admin / 123456`
- User(示例): `demo / 123456`

## ✅ Verification
1. 打开 http://localhost:3000，首页可看到至少 1 个示例业务功能卡片。
2. 点击"管理后台"并使用 `admin/123456` 登录。
3. 在"业务页面管理"上传 ZIP（含 `index.html`），系统将自动生成 `/pages/[timestamp-rand]/...` 路由。
4. 在"用户管理"创建、编辑、删除普通用户，验证权限控制与 CSRF 保护。
5. 在"系统设置"修改上传限制与允许类型，再次上传验证配置生效。
6. 使用"SQL 查询"执行 `SELECT` 语句验证数据库可观测能力。

## 📦 项目结构
```text
.
├── backend
│   ├── app
│   │   ├── routes           # 认证/页面管理/用户管理/设置/公开接口/数据接口
│   │   ├── services         # 上传解压、动态数据表、初始化 Seed
│   │   ├── models.py        # ORM 模型
│   │   └── schemas.py       # Pydantic 参数校验
│   ├── Dockerfile
│   └── requirements.txt
├── frontend
│   ├── src
│   │   ├── pages            # 首页、后台登录、后台各管理面板
│   │   ├── services         # Axios 实例与认证存储
│   │   └── components       # ErrorBoundary 等
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── docs/database_schema.md
```

## 🔐 安全设计摘要
- 认证鉴权: JWT + 管理员角色校验 + CSRF Token 双重校验（写操作）。
- 密码安全: `bcrypt` 哈希存储，禁明文。
- 登录防爆破: 失败次数限制 + 临时锁定（默认 5 次失败，锁 15 分钟）。
- 上传安全: 扩展名白名单 + 高危后缀黑名单 + MIME 校验 + 可执行文件签名拦截 + 路径穿越防护。
- 注入防护: 业务主流程采用 SQLAlchemy ORM / Core 表达式。
- XSS/基础安全头: `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy` 等。

## 🛡 安全优化建议
1. **HTTPS 强制化**：生产环境应配置 TLS 证书，启用 HSTS 头并强制 HTTPS 跳转，避免明文传输 JWT Token。
2. **Token 黑名单机制**：当前 JWT 依赖有效期过期，建议引入 Redis Token 黑名单，支持主动注销/强制下线。
3. **文件内容深度扫描**：上传文件可进一步集成 ClamAV 等病毒扫描引擎，对 ZIP 内容做恶意代码检测。
4. **API 限流（Rate Limiting）**：对关键接口（登录、文件上传、SQL 查询）开启请求频率限制，防止 DDoS/CC 攻击。
5. **敏感配置管理**：生产环境应使用 Vault/AWS Secrets Manager 管理密钥，避免环境变量明文泄露。
6. **SQL 查询沙箱**：当前 SQL 控制台仅做关键字过滤，建议引入独立只读数据库账号，从数据库权限层面限制写操作。
7. **上传目录隔离**：上传文件目录应配置 Nginx `location` 禁止执行脚本，防止上传 WebShell 被直接执行。
8. **审计日志增强**：关键操作（页面创建/删除、用户管理、配置修改）应记录完整审计日志，包含操作人、IP、时间、变更内容。
9. **CORS 策略收紧**：生产环境应限制 `Access-Control-Allow-Origin` 为具体域名，禁止通配符 `*`。
10. **依赖漏洞扫描**：CI/CD 流程集成 `pip-audit` 和 `npm audit`，定期检测三方库漏洞。

## 🚢 部署说明
1. 根据 `.env.example` 生成 `.env`（可选，未提供时使用 compose 默认值）。
2. 生产环境建议替换 `APP_SECRET_KEY`、`JWT_SECRET_KEY`、`ENCRYPTION_KEY`。
3. 执行 `docker compose up --build -d`。
4. 通过 `docker compose logs -f backend frontend db` 观察日志。

## 🔭 后续扩展方向
1. 多角色 RBAC（超级管理员/运营/审计）与细粒度接口权限。
2. 上传文件接入对象存储（OSS/S3/MinIO）并启用版本管理。
3. 接入审计日志与指标监控（Prometheus + Grafana + Loki）。
4. 为业务页面提供 API Key 生命周期管理（过期、吊销、轮转）。
5. 多用户权限协作：支持不同管理员管理不同业务页面分组。
6. 文件云存储：集成 MinIO/阿里云 OSS 替代本地文件存储。
7. 日志监控：集成 ELK/Loki 实现操作日志实时检索与告警。
