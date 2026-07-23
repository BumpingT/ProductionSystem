# 生产管理系统 (ProductionSystem) — v2.0

> 电气行业桌面生产记录管理系统 | Python Tkinter + SQLite
> 版本 2.0 | 2026-07 | 业务重构版

---

## 📋 v2.0 重构内容

| 模块 | 变更 |
|------|------|
| 📦 物料管理 | 去掉单价，改为 **编号 + 名称 + 版本**，支持多版本物料 |
| 👷 工人管理 | **树形结构**（班组→工人），班组下拉选择，班组独立管理 |
| 🔧 工序管理 | 去掉工人分配，物料**可搜索下拉**（显示"编号(名称)-版本"），工序可搜索下拉 |

---

## 📋 功能概览

| 功能 | 说明 |
|------|------|
| 🔐 用户登录 | 用户名密码验证，支持记住密码，三种角色 |
| 📝 生产记录 | 添加/删除/编辑记录，选择工人工序，自动计算工资 |
| 📦 物料管理 | 编号+名称+版本，关键字搜索，电气行业种子数据 |
| 👷 工人管理 | 树形结构(班组→工人)，班组下拉选择，班组独立管理 |
| 🔧 工序管理 | 物料可搜索下拉，工序可搜索下拉，无工人分配 |
| 👥 用户管理 | 系统用户增删改查（仅管理员） |
| 🔑 权限管理 | 按用户细粒度分配功能权限（仅管理员） |
| 📊 图表报告 | ECharts 生成工人工资排行、日产量趋势、工序分布图 |
| 📅 月度汇总 | 按月汇总各工人产量和工资 |
| 📈 汇总查询 | 按日期范围/工人筛选统计数据 |
| 📎 Excel 导出 | 统计结果导出为 .xlsx 文件 |
| 🔄 密码修改 | 当前用户可修改自己的密码 |

---

## 🚀 快速开始

### 环境要求
- **Python 3.10+**
- 操作系统：Windows 10/11

### 运行方式
```bash
# 1. 进入项目目录
cd production_system

# 2. （可选）安装 Excel 导出支持
pip install openpyxl

# 3. 直接运行
python main.py
```

### 默认账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | 管理员（全部权限） |

---

## 📁 项目结构

```
production_system/
├── main.py                      # 应用入口
├── config.py                    # 配置常量
├── requirements.txt             # 依赖列表
├── README.md                    # 本文件
├── build.py                     # 打包脚本
├── echarts.min.js               # ECharts 图表库
│
├── models/                      # 数据访问层
│   ├── database.py              # 数据库连接 + 初始化 + 种子数据(电气行业)
│   ├── material.py              # 物料 CRUD + 搜索 (code/name/version)
│   ├── worker.py                # 工人 CRUD + 班组管理
│   ├── process.py               # 工序 CRUD (material_code关联)
│   ├── record.py                # 生产记录 CRUD + 统计
│   └── user.py                  # 用户 + 权限 CRUD
│
├── services/                    # 业务逻辑层
│   ├── auth_service.py          # 登录验证、权限检查
│   ├── permission_service.py    # 数据权限
│   ├── material_service.py      # 物料服务
│   ├── worker_service.py        # 工人服务 + 班组管理
│   ├── process_service.py       # 工序服务 (无工人分配)
│   ├── stats_service.py         # 统计计算
│   ├── export_service.py        # Excel 导出
│   └── chart_service.py         # ECharts 图表生成
│
├── ui/                          # UI 层
│   ├── login_view.py            # 登录视图
│   ├── dashboard_view.py        # 主面板视图
│   ├── widgets/
│   │   └── crud_dialog_base.py  # CRUD 对话框基类
│   └── dialogs/
│       ├── material_dialog.py   # 物料管理 (code/name/version)
│       ├── worker_dialog.py     # 工人管理 (树形结构)
│       ├── process_dialog.py    # 工序管理 (搜索下拉)
│       ├── edit_record_dialog.py
│       ├── user_dialog.py
│       ├── change_password_dialog.py
│       └── permission_dialog.py
│
├── utils/                       # 工具层
│   ├── auth.py                  # 密码哈希 (PBKDF2-SHA256)
│   ├── logger.py                # 日志系统
│   └── error_handler.py         # 全局异常处理
│
└── tests/                       # 单元测试
    └── test_services/
        └── test_auth_service.py
```

---

## ⚙️ 打包为独立 exe

```bash
pip install pyinstaller
python build.py
```

打包后生成 `dist/生产管理系统.exe`，约 10MB，可独立运行。

---

## 🗄️ 数据库

- 数据库文件：`data.db`（自动在 exe 同级目录创建）
- 技术：SQLite 3，WAL 模式
- 首次运行自动建表并插入电气行业种子数据

### v2.0 表结构

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `materials` | 物料 | id, code, name, version |
| `workers` | 工人 | id, name, group_name |
| `groups` | 班组 | id, name |
| `processes` | 工序 | id, material_code, process_name, unit_price |
| `records` | 生产记录 | id, worker_id, process_id, quantity, unit_price, record_date |
| `users` | 系统用户 | id, username, password_hash, display_name, role |

---

## 📝 使用说明

### 基本操作流程
1. **登录** → 输入 `admin` / `admin123`
2. **添加记录** → 依次选择工人、工序、填写件数 → 点击"添加"
3. **管理物料** → 点击工具栏"管理物料" → 输入编号/名称/版本
4. **管理工人** → 点击工具栏"管理工人" → 树形浏览/添加班组和工人
5. **管理工序** → 点击工具栏"管理工序" → 搜索选择物料和工序名
6. **查看统计** → 点击"生成图表报告"在浏览器查看图表

### 权限说明
- **管理员 (admin)**：全部功能可用
- **班组长 (leader)**：除用户管理外全部可用
- **普通用户 (worker)**：仅查看和添加工人本人的记录

---

## 🔧 常见问题

**Q: 打开时报错 "no module named openpyxl"**
A: 导出 Excel 时需要 openpyxl，运行 `pip install openpyxl` 即可。

**Q: 如何重置数据？**
A: 删除 `data.db` 文件后重新运行程序，会自动重建数据库并插入种子数据。

**Q: 图表报告无法打开？**
A: 确保 `echarts.min.js` 与 `main.py` 在同一目录。

---

## 📄 日志

- 日志文件：`app.log`（与 exe 同级）
- 同时输出到控制台和文件

---

## 🔮 后续可扩展方向

- [ ] 物料BOM表（子物料组成）
- [ ] 班组KPI统计
- [ ] 工序工装/设备管理
- [ ] 数据备份与恢复
- [ ] 批量导入（从 Excel 导入物料和工人）
- [ ] Web 端查询（Flask + REST API）
