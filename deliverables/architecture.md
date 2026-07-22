# 生产管理系统 — 架构设计文档

> 版本 1.0 | 2026-07

---

## 1. 技术选型

### 1.1 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 编程语言 | Python | 3.10+ | 跨平台、开发效率高、生态丰富 |
| GUI 框架 | Tkinter (ttk) | 标准库 | 无需额外安装，轻量级，Windows 原生集成 |
| 数据库 | SQLite 3 | 标准库 | 零配置，单文件存储，适合桌面单机应用 |
| 图表 | ECharts | 5.x | 高性能 JS 图表库，通过 `webbrowser` 展示 |
| Excel 导出 | openpyxl | 3.x | 按需安装，读写 .xlsx 文件 |
| 打包工具 | PyInstaller | 6.x | 将 Python 应用打包为独立 exe |
| 日志 | logging (标准库) | - | 标准日志框架，支持多 handler |
| 密码学 | hashlib (标准库) | - | PBKDF2-SHA256 密码哈希 |

### 1.2 选型理由

| 选择 | 理由 |
|------|------|
| Python | 团队熟悉度最高，Tkinter GUI 开发最快捷 |
| Tkinter | 零依赖、与 Windows 原生外观一致、打包体积小（~10MB vs Electron ~150MB） |
| SQLite | 桌面单用户场景无需网络数据库，无部署成本 |
| ECharts | 功能丰富、交互流畅，HTML 方式可离线运行 |
| openpyxl | 纯 Python 读写 Excel，无需安装 Office |
| PBKDF2-SHA256 | 业界标准密码哈希算法，抗暴力破解 |

---

## 2. 系统分层架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                     UI 层 (ui/)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ main.py      │  │ dialogs/     │  │ widgets/         │  │
│  │ (入口+主窗口) │  │ material     │  │ crud_dialog_base │  │
│  │              │  │ worker       │  │ table_widget     │  │
│  │              │  │ process      │  │ stats_bar        │  │
│  │              │  │ user         │  │                  │  │
│  │              │  │ permission   │  │                  │  │
│  │              │  │ summary      │  │                  │  │
│  │              │  │ calendar     │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                           │                                  │
│                           ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                 业务逻辑层 (services/)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ AuthService  │  │ StatsService │  │ ExportService    │  │
│  │ (登录/权限)   │  │ (统计计算)    │  │ (Excel导出)      │  │
│  │              │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                           │              (ChartService)     │
│                           ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                 数据访问层 (models/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ MaterialRepo │  │ WorkerRepo   │  │ ProcessRepo      │  │
│  │ RecordRepo   │  │ UserRepo     │  │ Database (连接)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                           │                                  │
│                           ▼                                  │
├─────────────────────────────────────────────────────────────┤
│                   数据存储层                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                 SQLite (data.db)                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

                   工具层 (utils/)
┌─────────────────────────────────────────────────────────────┐
│  auth.py (密码哈希)  │  logger.py (日志)  │ error_handler   │
└─────────────────────────────────────────────────────────────┘

                   配置层 (config.py)
┌─────────────────────────────────────────────────────────────┐
│  颜色主题  │  路径配置  │  权限定义  │  角色定义             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各层职责

| 层次 | 职责 | 依赖 |
|------|------|------|
| **UI层** | 用户交互、事件处理、界面渲染 | → 调用 Service 层 |
| **Service层** | 业务逻辑编排、验证、计算 | → 调用 Repository 层 |
| **Repository层** | 数据 CRUD、SQL 封装 | → 调用 Database 连接 |
| **Database** | 连接管理、事务、表初始化 | → SQLite 文件 |
| **Utils** | 跨层通用工具函数 | 无业务依赖 |
| **Config** | 全局常量定义 | 无依赖 |

### 2.3 依赖方向

```
UI ──→ Service ──→ Repository ──→ Database
  │                    │
  └────→ Utils ←───────┘
         │
         └────→ Config
```

**核心原则**：依赖方向永远从上层指向下层，下层不依赖上层。

---

## 3. 模块设计

### 3.1 模块清单

| 模块 | 文件 | 类/函数 | 职责 |
|------|------|---------|------|
| **config** | `config.py` | - | 颜色、路径、权限、角色常量 |
| **models.database** | `models/database.py` | `Database` | 连接管理、表初始化、种子数据 |
| **models.material** | `models/material.py` | `MaterialRepository` | 物料 CRUD |
| **models.worker** | `models/worker.py` | `WorkerRepository` | 工人 CRUD |
| **models.process** | `models/process.py` | `ProcessRepository` | 工序 CRUD |
| **models.record** | `models/record.py` | `RecordRepository` | 记录 CRUD + 统计查询 |
| **models.user** | `models/user.py` | `UserRepository` | 用户 + 权限 CRUD |
| **services.auth** | `services/auth_service.py` | `AuthService` | 登录验证、密码修改、权限检查 |
| **services.stats** | `services/stats_service.py` | `StatsService` | 统计计算、月度汇总 |
| **services.export** | `services/export_service.py` | `export_excel()` | Excel 导出 |
| **services.chart** | `services/chart_service.py` | `_chart_html()`, `gen_report()` | 图表 HTML 生成 |
| **utils.auth** | `utils/auth.py` | `hash_password()`, `verify_password()` | 密码哈希 |
| **utils.logger** | `utils/logger.py` | `logger` | 日志实例 |
| **utils.error_handler** | `utils/error_handler.py` | `setup_global_handler()`, `safe_call()` | 全局异常处理 |
| **ui.widgets.crud_base** | `ui/widgets/crud_dialog_base.py` | `CrudDialogBase` | CRUD 对话框基类 |
| **ui.dialogs.material** | `ui/dialogs/material_dialog.py` | `MaterialDialog` | 物料管理对话框 |
| **ui.dialogs.worker** | `ui/dialogs/worker_dialog.py` | `WorkerDialog` | 工人管理对话框 |
| **ui.dialogs.process** | `ui/dialogs/process_dialog.py` | `ProcessDialog` | 工序管理+工人分配 |
| **main** | `main.py` | `App` | 应用入口+主窗口UI |

### 3.2 接口定义

```
┌─────────────────────────────────────────────────────┐
│                  Service 层接口                       │
├─────────────────────────────────────────────────────┤
│ AuthService                                         │
│   +login(username, password) → dict|None            │
│   +change_password(un, old, new) → (bool, str)      │
│   +get_permissions(username) → dict                 │
│   +has_permission(username, perm_key) → bool        │
│                                                     │
│ StatsService                                        │
│   +get_summary(start, end, process, worker) → dict  │
│   +get_monthly_stats(month) → dict                  │
│   +list_months() → list[str]                        │
│                                                     │
│ export_excel(stats, filepath, title) → bool         │
│ gen_report(stats, title) → None  (opens browser)    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                Repository 层接口                      │
├─────────────────────────────────────────────────────┤
│ MaterialRepository                                  │
│   +get_all() → list[dict]                           │
│   +add(name, price) → bool                          │
│   +update(id, name, price)                          │
│   +delete(id)                                       │
│                                                     │
│ WorkerRepository                                    │
│   +get_all() → list[dict]                           │
│   +add(name, group) → bool                          │
│   +update(id, name, group)                          │
│   +delete(id)                                       │
│                                                     │
│ ProcessRepository                                   │
│   +get_all() → list[dict]                           │
│   +add(material, process_name, unit_price) → bool   │
│   +update(id, material, process_name, unit_price)   │
│   +delete(id)                                       │
│                                                     │
│ RecordRepository                                    │
│   +get_all(user) → list[dict]                       │
│   +add(worker_id, process_id, qty, price, date)→bool│
│   +update(id, worker_id, process_id, qty, price, dt)│
│   +delete(id)                                       │
│   +get_stats(start, end, process, worker) → dict    │
│   +list_months() → list[str]                        │
│   +get_worker_processes(worker_id) → list[int]      │
│   +assign_worker_process(worker_id, process_id)     │
│   +unassign_worker_process(worker_id, process_id)   │
│                                                     │
│ UserRepository                                      │
│   +get_all() → list[dict]                           │
│   +get_by_username(username) → dict|None            │
│   +get_by_worker_id(worker_id) → dict|None          │
│   +add(username, password, display_name, role, wid) │
│   +update_password(username, new_password)          │
│   +update_profile(username, display, role, worker)  │
│   +delete(username) → bool                          │
│   +get_permissions(username) → dict                 │
│   +set_permission(username, perm_key, allowed)      │
└─────────────────────────────────────────────────────┘
```

---

## 4. 数据设计

### 4.1 数据库表结构

```sql
-- 物料表
CREATE TABLE materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    price       REAL DEFAULT 0
);

-- 工人表
CREATE TABLE workers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    group_name  TEXT NOT NULL DEFAULT ''
);

-- 工序表
CREATE TABLE processes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    material     TEXT NOT NULL,
    process_name TEXT NOT NULL,
    unit_price   REAL NOT NULL DEFAULT 0,
    UNIQUE(material, process_name)
);

-- 工人工序分配表
CREATE TABLE worker_processes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id   INTEGER NOT NULL,
    process_id  INTEGER NOT NULL,
    UNIQUE(worker_id, process_id)
);

-- 生产记录表
CREATE TABLE records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id    INTEGER NOT NULL DEFAULT 0,
    process_id   INTEGER NOT NULL DEFAULT 0,
    quantity     REAL NOT NULL,
    unit_price   REAL NOT NULL,
    record_date  TEXT NOT NULL,
    created_at   TEXT DEFAULT (datetime('now','localtime'))
);

-- 用户表
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'worker',
    worker_id     INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now','localtime'))
);

-- 用户权限表
CREATE TABLE user_permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL,
    perm_key    TEXT NOT NULL,
    allowed     INTEGER NOT NULL DEFAULT 0,
    UNIQUE(username, perm_key)
);

-- 设置表
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
```

### 4.2 数据流设计

#### 登录流程

```
用户输入凭据 → main.py:do_login()
                    │
                    ▼
              AuthService.login(un, pw)
                    │
                    ├─→ UserRepository.get_by_username(un)
                    │       │
                    │       ▼
                    │   [返回用户记录 或 None]
                    │
                    ├─→ utils.auth.verify_password(pw, hash)
                    │       │
                    │       ▼
                    │   [True / False]
                    │
                    ▼
               [登录成功/失败]
                    │
                    ▼
              UserRepository.get_permissions(un)
                    │
                    ▼
              self.current_user = user
              self.user_perms = perms
                    │
                    ▼
              build_ui() → refresh() → _apply_permissions()
```

#### 添加记录流程

```
用户填写表单 → main.py:do_add()
                    │
                    ├─→ 获取 worker_id, process_id, qty, date
                    │
                    ├─→ RecordRepository.add(wid, pid, qty, price, date)
                    │       │
                    │       ▼
                    │   INSERT INTO records ...
                    │   commit()
                    │
                    └─→ refresh()
                            │
                            ├─→ RecordRepository.get_all(user)
                            ├─→ RecordRepository.get_stats()
                            │
                            ▼
                        刷新表格 + 统计卡片
```

#### 图表报表流程

```
用户点击"生成图表报告" → main.py:open_chart()
                              │
                              ▼
                        RecordRepository.get_stats()
                              │
                              ▼
                        chart_service.gen_report(stats, title)
                              │
                              ├─→ _chart_html(stats) → HTML string
                              ├─→ 写入 tempfile/report.html
                              ├─→ 复制 echarts.min.js 到 temp 目录
                              └─→ webbrowser.open('file://...')
```

---

## 5. 错误处理策略

### 5.1 层级错误处理

| 层级 | 策略 | 实现 |
|------|------|------|
| UI 层 | try-except + messagebox 弹窗 | 每个回调函数内捕获 |
| Service 层 | 返回 (bool, str) 元组或 None | 上层检查返回值 |
| Repository 层 | try-except 记录日志 + 返回 False/None | `logger.warning/error` |
| 全局未捕获 | `sys.excepthook` + tkinter 钩子 | `error_handler.setup_global_handler()` |

### 5.2 日志方案

```
日志级别: DEBUG < INFO < WARNING < ERROR < CRITICAL

输出目标:
  ├── 控制台 (stderr) → 即时查看
  └── 文件 app.log → 持久化排查

日志格式:
  控制台: %(asctime)s [%(levelname)s] %(name)s: %(message)s
  文件:   %(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s

使用方式:
  from utils.logger import logger
  logger.info('用户登录成功')
  logger.warning('登录失败: 密码错误')
  logger.error(f'数据库错误: {e}', exc_info=True)
```

### 5.3 密码安全

- 使用 PBKDF2-SHA256 哈希，100,000 次迭代
- 使用 32 字符随机 salt（hex 编码）
- 存储格式：`salt(32) + hash(64)` 共 96 字符
- 记住密码功能使用 Base64 编码本地文件存储（仅本地使用）

---

## 6. 性能考虑

- 记录列表限制 500 条（`LIMIT 500`），避免大数据量卡顿
- 数据库使用 WAL 模式（`PRAGMA journal_mode=WAL`）提升并发
- 统计查询使用 SQL 聚合函数，避免 Python 层计算
- ECharts 图表通过本地 HTML 渲染，不占用 GUI 线程

---

## 7. 部署方案

```
打包命令: pyinstaller --onefile --windowed --add-data "echarts.min.js;." main.py

输出: dist/ProductionSystem.exe (~10MB)

运行依赖:
  ├── Python 标准库 (自带)
  ├── openpyxl (可选，导出Excel时需要)
  └── echarts.min.js (打包在exe中)
```

---

## 8. 假设点

- 应用运行在 Windows 10/11 环境
- 单用户模式，无网络通信需求
- 数据库文件 `data.db` 与 exe 同级目录
- 日志文件 `app.log` 与 exe 同级目录
