# 生产管理系统 — 架构设计文档（v2.0 业务重构）

> 版本 2.0 | 2026-07

---

## 1. 技术选型（保持不变）

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 编程语言 | Python | 3.10+ | 无变化 |
| GUI 框架 | Tkinter (ttk) | 标准库 | 无变化 |
| 数据库 | SQLite 3 | 标准库 | 无变化 |
| 图表 | ECharts | 5.x | 无变化 |
| Excel 导出 | openpyxl | 3.x | 无变化 |
| 日志 | logging | 标准库 | 无变化 |
| 密码 | PBKDF2-SHA256 | 标准库 | 无变化 |

---

## 2. 分层架构（保持不变）

```
UI 层 (ui/)          →  对话框、主面板
Service 层 (services/) →  业务逻辑编排
Repository 层 (models/) → 数据 CRUD
Database (SQLite)      →  持久存储
Utils (utils/)         →  工具函数
```

---

## 3. 数据库表结构变更

### 3.1 materials 表重构

```sql
-- 原表（v1.0）
CREATE TABLE materials (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    price REAL DEFAULT 0
);

-- 新表（v2.0）
CREATE TABLE materials (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT NOT NULL UNIQUE,       -- 物料编号，如 TR-001
    name    TEXT NOT NULL,              -- 物料名称，如 变压器
    version TEXT NOT NULL DEFAULT '',   -- 版本，如 V1.0
    UNIQUE(name, version)              -- 同一名称+版本唯一
);
```

**迁移说明**：
- 去掉 price 字段
- 增加 code（编号）和 version（版本）字段
- 旧数据不再兼容，数据库需重建（种子数据重新插入）

### 3.2 processes 表调整

```sql
-- 原表（v1.0）
CREATE TABLE processes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    material     TEXT NOT NULL,          -- 物料名称（旧）
    process_name TEXT NOT NULL,
    unit_price   REAL NOT NULL DEFAULT 0,
    UNIQUE(material, process_name)
);

-- 新表（v2.0）
CREATE TABLE processes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code  TEXT NOT NULL,        -- 物料编号（引用materials.code）
    material_name  TEXT NOT NULL DEFAULT '',  -- 物料名称冗余（用于显示）
    material_version TEXT NOT NULL DEFAULT '', -- 物料版本冗余
    process_name   TEXT NOT NULL,
    unit_price     REAL NOT NULL DEFAULT 0,
    UNIQUE(material_code, process_name)
);
```

**设计考量**：
- 存储 material_code 引用 materials 表，同时冗余存储 name 和 version
- 冗余存储避免了每次查询都需要 JOIN，且删除物料后工序仍可显示历史信息
- 工序列表查询时，物料显示为 "编号(名称)-版本" 格式

### 3.3 worker_processes 表移除

```sql
-- 原表（v1.0）—— 删除
DROP TABLE IF EXISTS worker_processes;
```

工序的工人分配功能已去除，此表及所有相关代码一并移除。

### 3.4 workers 表保持不变

```sql
CREATE TABLE workers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    group_name  TEXT NOT NULL DEFAULT ''
);
```

### 3.5 班组管理（新增独立管理）

不新增表，利用 workers 表的 group_name 字段。
从 workers 表中 SELECT DISTINCT group_name 获取所有班组列表。
支持班组 CRUD：
- 添加班组：写入一条占位记录（或单独管理）
- 删除班组：删除该班组下所有工人

实际实现方式：
- 班组信息存储在 workers 表的 group_name 中
- 添加班组时，向 workers 插入一条特殊记录（name='__group__', group_name='班组名'）
- 或者更简单：班组不单独存表，直接从 workers.group_name 中 DISTINCT 获取

**更优方案**：新建 groups 表

```sql
CREATE TABLE groups (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
```

同时 workers 表增加 group_id 引用 groups.id：

```sql
ALTER TABLE workers ADD COLUMN group_id INTEGER DEFAULT 0;
```

这样班组可以独立管理，工人通过 group_id 关联班组。

但为了最小化改动，使用 workers.group_name 文本字段配合 DISTINCT 获取班组列表，在 UI 层面实现树形展示。

**最终决定**：不新增 groups 表，使用 workers.group_name 配合 DISTINCT 去重获取班组列表。树形结构在 UI 层面实现。

### 3.6 其他表保持不变

records、users、user_permissions、settings、leader_workers 表结构不变。

---

## 4. 模块接口变更

### 4.1 MaterialRepository 接口变更

```python
# 旧接口
class MaterialRepository:
    get_all() → list[dict]           # {id, name, price}
    add(name, price) → bool
    update(mid, name, price)
    delete(mid)

# 新接口
class MaterialRepository:
    get_all() → list[dict]           # {id, code, name, version}
    add(code, name, version) → bool
    update(mid, code, name, version)
    delete(mid)
    get_by_code(code) → dict|None    # 新增：按编号查询
    search(keyword) → list[dict]     # 新增：关键字搜索
```

### 4.2 ProcessRepository 接口变更

```python
# 旧接口
class ProcessRepository:
    get_all() → list[dict]           # {id, material, process_name, unit_price, material_price}
    add(material, process_name, unit_price) → bool
    update(pid, material, process_name, unit_price)
    delete(pid)
    # 工人工序分配
    get_worker_processes(worker_id) → list[int]
    assign_worker_process(worker_id, process_id)
    unassign_worker_process(worker_id, process_id)

# 新接口
class ProcessRepository:
    get_all() → list[dict]           # {id, material_code, material_name, material_version, process_name, unit_price}
    add(material_code, process_name, unit_price) → bool
    update(pid, material_code, process_name, unit_price)
    delete(pid)
    get_process_names() → list[str]  # 新增：获取所有不重复的工序名
```

**移除**：get_worker_processes、assign_worker_process、unassign_worker_process

### 4.3 WorkerRepository 接口变更

```python
# 旧接口
class WorkerRepository:
    get_all() → list[dict]           # {id, name, group_name}
    add(name, group) → bool
    update(wid, name, group)
    delete(wid)

# 新接口（新增班组相关方法）
class WorkerRepository:
    get_all() → list[dict]           # {id, name, group_name}
    add(name, group) → bool
    update(wid, name, group)
    delete(wid)
    get_groups() → list[str]         # 新增：获取所有班组（DISTINCT group_name）
    add_group(group_name) → bool     # 新增：添加班组
    delete_group(group_name) → bool  # 新增：删除班组（连带删除组内工人）
```

### 4.4 ProcessService 接口变更

```python
# 旧接口
class ProcessService:
    get_all()
    add(material, process_name, unit_price)
    update(pid, material, process_name, unit_price)
    delete(pid)
    get_worker_processes(worker_id)
    assign_worker(worker_id, process_id)
    unassign_worker(worker_id, process_id)

# 新接口
class ProcessService:
    get_all()
    add(material_code, process_name, unit_price)
    update(pid, material_code, process_name, unit_price)
    delete(pid)
    get_process_names() → list[str]  # 新增
```

### 4.5 WorkerService 接口变更

```python
# 新接口
class WorkerService:
    get_all()
    add(name, group)
    update(wid, name, group)
    delete(wid)
    get_groups() → list[str]         # 新增
    add_group(group_name) → bool     # 新增
    delete_group(group_name) → bool  # 新增
```

---

## 5. 数据流变更

### 5.1 物料管理数据流

```
用户输入编号/名称/版本 → MaterialDialog.on_add()
    │
    ▼
MaterialService.add(code, name, version)
    │
    ▼
MaterialRepository.add(code, name, version)
    │
    ▼
INSERT INTO materials (code, name, version) VALUES (?, ?, ?)
```

### 5.2 工人管理数据流（树形结构）

```
打开对话框 → WorkerDialog.refresh()
    │
    ├─ WorkerRepository.get_groups() → ["装配组","测试组",...]
    │       │
    │       ▼  Treeview 插入班组父节点
    │
    └─ WorkerRepository.get_all()
            │
            ▼  Treeview 插入工人子节点（按班组分组）

添加工人 → on_add()
    │
    ├─ 选择班组（下拉框）
    ├─ 输入姓名
    ▼
WorkerRepository.add(name, group_name)
```

### 5.3 工序管理数据流（搜索+选择）

```
打开对话框 → ProcessDialog.refresh()
    │
    ├─ MaterialRepository.get_all() → 填入物料下拉
    └─ ProcessRepository.get_all() → 填入工序列表

选择物料 → 下拉搜索过滤
    │
    ▼
输入关键字 → 实时过滤物料列表（按 code/name 匹配）

添加工序 → on_add()
    │
    ├─ 物料下拉选中值 → material_code
    ├─ 工序名下拉/输入 → process_name
    ├─ 单价输入 → unit_price
    ▼
ProcessRepository.add(material_code, process_name, unit_price)
```

---

## 6. UI 组件变更

### 6.1 MaterialDialog 重构

| 项目 | 旧 | 新 |
|------|-----|-----|
| 列 | 名称、单价 | 编号、名称、版本 |
| 添加字段 | 名称 | 编号、名称、版本 |
| 基类 | CrudDialogBase | CrudDialogBase（保持不变） |

### 6.2 WorkerDialog 重构

| 项目 | 旧 | 新 |
|------|-----|-----|
| 显示方式 | 平面表格 | 树形结构（班组→工人） |
| 列表控件 | ttk.Treeview（表格模式） | ttk.Treeview（树模式） |
| 添加字段 | 姓名、组别(文本框) | 姓名、班组(下拉选择) |
| 新功能 | 无 | 添加班组、删除班组按钮 |

### 6.3 ProcessDialog 重构

| 项目 | 旧 | 新 |
|------|-----|-----|
| 物料输入 | 文本框(自由输入) | Combobox(可搜索下拉) |
| 工序输入 | 文本框(自由输入) | Combobox(可搜索+可输入) |
| 工人分配 | 复选框列表区域 | ❌ 完全移除 |
| 列表列 | 物料、工序、单价 | 物料、工序、单价 |
| 物料显示 | 物料名 | 编号(名称)-版本 |

---

## 7. dashboard_view.py 变更

主界面 "添加记录" 表单中，工序下拉列表的显示格式改为：
```
TR-001(变压器)-V1.0 / 绕线
CONT-01(接触器)-A型 / 组装
```

对应修改 `_on_worker_sel` 和 `_on_process_sel` 中的工序文本组装逻辑。

---

## 8. 错误处理与日志方案（保持不变）

- UI 层：try-except + messagebox
- Service 层：返回 (bool, str) 或 None
- Repository 层：logger.warning + 返回 False/None
- 全局处理：sys.excepthook 钩子

---

## 9. 数据迁移策略

由于表结构发生 breaking changes，需要删除旧数据库文件重新初始化：

```python
# database.py 中增加版本检测
# 如果数据库版本不匹配，提示用户备份后重建
```

实际采用方式：直接修改建表 SQL，删除旧 data.db 自动重建新表。
种子数据更新为电气行业数据。

---

## 10. 性能考虑

- 班组树形结构加载：一次性加载所有工人，在 Python 层面分组
- 物料搜索：在 Python 层面过滤（数据量小，<1000条不需要数据库LIKE）
- 工序下拉缓存：物料和工序名列表在打开对话框时一次性加载
