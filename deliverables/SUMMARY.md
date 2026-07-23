# 生产管理系统 — 项目总结（v2.0 业务重构）

> 桌面应用全流程开发 | 2026-07 | 电气行业专用

---

## 1. 项目概览

**生产管理系统 (ProductionSystem)** 是一个基于 Python Tkinter + SQLite 的桌面生产记录管理应用，专为电气制造企业设计。

### v2.0 业务重构内容

| 模块 | 变更内容 |
|------|---------|
| 📦 物料管理 | 去掉单价，改为 **编号 + 名称 + 版本** 三维结构，支持电气行业多版本物料 |
| 👷 工人管理 | 改为 **树形结构（班组→工人）**，班组改为下拉选择，支持独立班组管理 |
| 🔧 工序管理 | 去掉工人分配，物料改为**可搜索下拉选择**（显示"编号(名称)-版本"），工序改为可搜索下拉 |

---

## 2. 实现功能

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 🔐 用户登录 | ✅ 完成 | 用户名密码验证、记住密码、三种角色 |
| 📝 生产记录 | ✅ 完成 | 添加/删除/编辑记录、选择工序、自动计算工资 |
| 📦 物料管理 | ✅ **重构** | 编号+名称+版本，关键字搜索，电气行业种子数据 |
| 👷 工人管理 | ✅ **重构** | 树形结构(班组→工人)，班组下拉选择，班组独立管理 |
| 🔧 工序管理 | ✅ **重构** | 物料可搜索下拉，工序可搜索下拉，去除工人分配 |
| 👥 用户管理 | ✅ 完成 | 系统用户增删改查（仅管理员） |
| 🔑 权限管理 | ✅ 完成 | 按用户细粒度分配功能权限 |
| 📊 图表报告 | ✅ 完成 | ECharts 生成工人工资排行、日产量趋势、工序分布图 |
| 📅 月度汇总 | ✅ 完成 | 按月汇总各工人产量和工资 |
| 📈 汇总查询 | ✅ 完成 | 按日期范围/工人筛选统计数据 |
| 📎 Excel 导出 | ✅ 完成 | 统计结果和表格导出为 .xlsx 文件 |
| 🔄 密码修改 | ✅ 完成 | PBKDF2-SHA256 密码哈希 |

---

## 3. 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 编程语言 | Python | 3.10+ |
| GUI 框架 | Tkinter (ttk) | 标准库 |
| 数据库 | SQLite 3 | 标准库 |
| 图表 | ECharts | 5.x |
| Excel 导出 | openpyxl | 3.x（可选） |
| 密码哈希 | PBKDF2-SHA256 | 标准库 |
| 日志 | logging | 标准库 |
| 打包 | PyInstaller | 6.x |

---

## 4. 项目结构

```
production_system/
├── main.py                  # 应用入口
├── config.py                # 配置常量
├── requirements.txt         # 依赖
├── README.md                # 使用说明
├── echarts.min.js           # ECharts 图表库
│
├── models/                  # 数据访问层
│   ├── database.py          #   数据库连接 + 初始化 + 种子数据(电气行业)
│   ├── material.py          #   物料 CRUD + 搜索 (code/name/version)
│   ├── worker.py            #   工人 CRUD + 班组管理
│   ├── process.py           #   工序 CRUD (material_code关联)
│   ├── record.py            #   生产记录 CRUD + 统计
│   └── user.py              #   用户 + 权限 CRUD
│
├── services/                # 业务逻辑层
│   ├── auth_service.py      #   登录验证
│   ├── permission_service.py #   数据权限
│   ├── material_service.py  #   物料服务
│   ├── worker_service.py    #   工人服务 + 班组管理
│   ├── process_service.py   #   工序服务 (无工人分配)
│   ├── stats_service.py     #   统计
│   ├── export_service.py    #   Excel导出
│   └── chart_service.py     #   ECharts图表
│
├── ui/                      # UI 组件层
│   ├── login_view.py        #   登录视图
│   ├── dashboard_view.py    #   主面板视图
│   ├── widgets/
│   │   └── crud_dialog_base.py  # CRUD基类
│   └── dialogs/
│       ├── material_dialog.py   # 物料管理(code/name/version)
│       ├── worker_dialog.py     # 工人管理(树形结构)
│       ├── process_dialog.py    # 工序管理(搜索下拉)
│       ├── edit_record_dialog.py
│       ├── user_dialog.py
│       ├── change_password_dialog.py
│       └── permission_dialog.py
│
└── utils/                   # 工具层
    ├── auth.py              #   密码哈希
    ├── logger.py            #   日志
    └── error_handler.py     #   异常处理
```

---

## 5. 如何运行

```bash
# 1. 确保 Python 3.10+
python --version

# 2. 安装依赖（可选）
pip install openpyxl  # Excel导出支持

# 3. 运行应用
python main.py

# 4. 默认管理员账号
#    用户名: admin
#    密码:   admin123
```

---

## 6. 后续可扩展方向

| 方向 | 说明 |
|------|------|
| 物料BOM表 | 支持物料清单（子物料组成） |
| 班组KPI | 班组级别产量和效率统计 |
| 工序工装管理 | 为工序关联工装/设备 |
| 数据备份 | 自动/手动备份 data.db |
| 批量导入 | 从 Excel 批量导入物料和工人 |
