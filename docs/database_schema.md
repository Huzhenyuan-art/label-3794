# 数据库结构设计（MySQL utf8mb4）

## 1) admin（管理员表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(64) | UNIQUE, INDEX | 管理员账号 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| last_login_at | DATETIME | NULL | 最近登录时间 |
| failed_login_attempts | INT | NOT NULL, DEFAULT 0 | 连续失败次数 |
| locked_until | DATETIME | NULL | 锁定截止时间 |
| created_at | DATETIME | NOT NULL | 创建时间（北京时间） |
| updated_at | DATETIME | NOT NULL | 更新时间（北京时间） |

## 2) user（普通用户表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(64) | UNIQUE, INDEX | 用户账号 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| display_name | VARCHAR(64) | NULL | 显示名称 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'active' | 状态（active/disabled） |
| last_login_at | DATETIME | NULL | 最近登录时间 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 3) business_pages（业务页面表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(120) | INDEX, NOT NULL | 功能名称 |
| description | TEXT | NOT NULL | 功能简介 |
| category | VARCHAR(64) | INDEX, NOT NULL | 业务分类 |
| developer | VARCHAR(64) | NOT NULL | 开发者 |
| main_page | VARCHAR(255) | NOT NULL | 主页面名称（如 index.html） |
| storage_folder | VARCHAR(255) | NOT NULL | 存储目录（如 static/pages/1750000000-8a7b9c） |
| route_path | VARCHAR(255) | UNIQUE, NOT NULL | 唯一路由（如 /pages/.../index.html） |
| table_prefix | VARCHAR(40) | UNIQUE, NOT NULL | 页面独立表前缀 |
| table_name | VARCHAR(80) | UNIQUE, NOT NULL | 页面独立数据表名 |
| api_token_hash | VARCHAR(64) | NOT NULL | 页面 API Token 的 SHA-256 哈希 |
| status | VARCHAR(16) | INDEX, NOT NULL | 启用状态（enabled/disabled） |
| uploader_admin_id | INT | FK -> admin.id | 上传管理员 |
| created_at | DATETIME | INDEX, NOT NULL | 添加时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 4) db_config（数据库配置表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| host | VARCHAR(128) | NOT NULL | 数据库地址 |
| port | INT | NOT NULL | 端口 |
| username | VARCHAR(128) | NOT NULL | 用户名 |
| password_encrypted | VARCHAR(255) | NOT NULL | 加密存储后的密码（Fernet） |
| database_name | VARCHAR(128) | NOT NULL | 数据库名 |
| table_prefix_rule | VARCHAR(64) | NOT NULL | 表前缀规则（如 page_{page_id}_） |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 5) system_settings（系统设置表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| upload_size_limit_mb | INT | NOT NULL, DEFAULT 100 | 上传大小限制 |
| allowed_extensions | JSON | NOT NULL | 允许后缀白名单 |
| allowed_mime_types | JSON | NOT NULL | 允许 MIME 白名单 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 6) login_audit（登录审计表）
| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(64) | NOT NULL | 登录用户名 |
| ip_address | VARCHAR(64) | NULL | 来源 IP |
| success | BOOLEAN | NOT NULL | 是否成功 |
| reason | VARCHAR(255) | NULL | 失败/成功原因 |
| attempted_at | DATETIME | INDEX, NOT NULL | 尝试时间 |

## 7) 动态业务数据表（每页面独立）
命名规则: `{table_prefix}_records`（示例：`pg17724430545846_records`）

| 字段名 | 类型 | 约束/索引 | 说明 |
|---|---|---|---|
| id | INT | PK, AUTO_INCREMENT | 主键 |
| record_key | VARCHAR(128) | UNIQUE, INDEX | 业务主键（页面内唯一） |
| payload | JSON | NOT NULL | 业务数据 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |
