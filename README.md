# 生产管理系统 (ProductionSystem)

基于 Python Tkinter + SQLite 的桌面生产记录管理系统，用于工厂车间记录工人产量、计算工资、生成统计图表。

---

## 📋 功能概览

| 功能 | 说明 |
|------|------|
| 🔐 用户登录 | 用户名密码验证，支持记住密码，三种角色（管理员/班组长/普通用户） |
| 📝 生产记录 | 添加/删除生产记录，选择工人和工序，自动计算工资 |
| 📦 物料管理 | 物料名称和单价的增删改查 |
| 👷 工人管理 | 工人姓名和组别的增删改查 |
| 🔧 工序管理 | 工序的增删改查 + 为工序分配可执行工人 |
| 👥 用户管理 | 系统用户的增删改查（仅管理员） |
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
# 1. 克隆或解压项目
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
├── main.py                      # 应用入口 + 主窗口 UI
├── config.py                    # 配置（颜色、路径、权限常量）
├── requirements.txt             # 依赖列表
├── README.md                    # 本文件
├── build.py                     # 打包脚本
├── echarts.min.js               # ECharts 图表库
│
├── models/                      # 数据访问层
│   ├── __init__.py
│   ├── database.py              # 数据库连接管理 + 表初始化
│   ├── material.py              # 物料 CRUD
│   ├── worker.py                # 工人 CRUD
│   ├── process.py               # 工序 CRUD
│   ├── record.py                # 生产记录 CRUD + 统计
│   └── user.py                  # 用户 + 权限 CRUD
│
├── services/                    # 业务逻辑层
│   ├── __init__.py
│   ├── auth_service.py          # 登录验证、权限检查
│   ├── stats_service.py         # 统计计算
│   ├── export_service.py        # Excel 导出
│   └── chart_service.py         # ECharts 图表生成
│
├── ui/                          # UI 层
│   ├── __init__.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── crud_dialog_base.py  # CRUD 对话框基类
│   └── dialogs/
│       ├── __init__.py
│       ├── material_dialog.py   # 物料管理对话框
│       ├── worker_dialog.py     # 工人管理对话框
│       └── process_dialog.py    # 工序管理对话框（含工人分配）
│
├── utils/                       # 工具层
│   ├── __init__.py
│   ├── auth.py                  # 密码哈希（PBKDF2-SHA256）
│   ├── logger.py                # 日志系统
│   └── error_handler.py         # 全局异常处理
│
└── tests/                       # 单元测试
    ├── __init__.py
    ├── conftest.py
    └── test_services/
        ├── __init__.py
        └── test_auth_service.py
```

---

## ⚙️ 打包为独立 exe

```bash
# 安装打包工具
pip install pyinstaller

# 执行打包
python build.py

# 或直接运行 PyInstaller
pyinstaller --onefile --windowed --add-data "echarts.min.js;." --name "生产管理系统" main.py
```

打包后生成 `dist/生产管理系统.exe`，约 10MB，可独立运行于没有 Python 环境的 Windows 系统。

---

## 🗄️ 数据库

- 数据库文件：`data.db`（自动在 exe 同级目录创建）
- 技术：SQLite 3，WAL 模式
- 首次运行自动建表并插入种子数据

### 表结构

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `materials` | 物料 | id, name, price |
| `workers` | 工人 | id, name, group_name |
| `processes` | 工序 | id, material, process_name, unit_price |
| `worker_processes` | 工人工序分配 | id, worker_id, process_id |
| `records` | 生产记录 | id, worker_id, process_id, quantity, unit_price, record_date |
| `users` | 系统用户 | id, username, password_hash, display_name, role |
| `user_permissions` | 用户权限 | id, username, perm_key, allowed |

---

## 📝 使用说明

### 基本操作流程

1. **登录** → 输入 `admin` / `admin123`
2. **添加记录** → 依次选择工人、工序、填写件数、确认日期 → 点击"添加"
3. **查看统计** → 点击"生成图表报告"在浏览器查看图表
4. **管理基础数据** → 点击工具栏按钮管理物料/工人/工序
5. **月度汇总** → 点击"月度汇总"选择月份查看
6. **汇总查询** → 点击"汇总查询"按日期/工人筛选

### 权限说明

- **管理员 (admin)**：全部功能可用
- **班组长 (leader)**：除用户管理外全部可用
- **普通用户 (worker)**：仅查看和添加工人本人的记录

---

## 🔧 常见问题

**Q: 打开时报错 "no module named openpyxl"**
A: 导出 Excel 时需要 openpyxl，运行 `pip install openpyxl` 即可。不影响其他功能。

**Q: 如何重置管理员密码？**
A: 删除 `data.db` 文件后重新运行程序，会自动创建默认管理员账号 `admin/admin123`。

**Q: 图表报告无法打开？**
A: 确保 `echarts.min.js` 与 `main.py` 在同一目录。

---

## 📄 日志

- 日志文件：`app.log`（与 exe 同级）
- 记录级别：INFO 及以上
- 同时输出到控制台和文件

---

## 🔮 后续可扩展方向

- [ ] 记录编辑功能（双击表格行编辑）
- [ ] 数据筛选（按日期/工人/工序过滤主表格）
- [ ] 导出当前表格到 Excel
- [ ] 数据备份与恢复
- [ ] Web 端查询（Flask + REST API）
- [ ] 批量导入（从 Excel 导入记录）
- [ ] 自定义报表模板
