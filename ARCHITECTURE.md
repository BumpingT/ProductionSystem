# 生产管理系统 — 架构重构方案

> 基于 `main.py`（v42，~1071 行）的架构分析与重构路线图

---

## 1. 现状总览

当前应用是一个**单文件、单体架构**的 Tkinter + SQLite 桌面应用。所有代码（UI、业务逻辑、数据访问）全部集中在 `main.py` 中。

```
main.py (1071 行)
├── 全局变量 / 配置       (约 30 行)
├── 工具函数              (约 40 行)
├── 数据访问层 (全局函数)  (约 280 行)
├── App 类 (全部 UI)      (约 700 行)
└── 入口                  (约 10 行)
```

### 痛点总结

| 维度 | 评分 | 核心问题 |
|------|:----:|----------|
| 架构合理性 | 9/10 | 无分层，UI/业务/数据完全耦合 |
| 可维护性 | 8/10 | 单文件超千行，闭包回调嵌套难以调试 |
| 可测试性 | 9/10 | 无法编写任何单元测试 |
| 错误处理 | 8/10 | 静默吞异常，无全局处理器 |
| 安全性 | 6/10 | Base64 凭据，SQLite 无加密 |
| 可扩展性 | 9/10 | 新增功能需改多处代码 |
| 可观测性 | 10/10 | 完全没有日志 |
| 构建/部署 | 7/10 | 22 个版本，无自动化 |

---

## 2. 目标架构

### 整体结构

```
production_system/
├── main.py                        # 应用入口
├── config.py                      # 配置（路径、颜色、默认值）
├── models/                        # 数据模型 + 数据访问层
│   ├── __init__.py
│   ├── database.py                # 连接管理 + Repository 基类
│   ├── material.py                # 物料 CRUD
│   ├── worker.py                  # 工人 CRUD
│   ├── process.py                 # 工序 CRUD
│   ├── record.py                  # 生产记录 CRUD + 统计
│   └── user.py                    # 用户 + 权限 CRUD
├── services/                      # 业务逻辑层
│   ├── __init__.py
│   ├── auth_service.py            # 登录、密码、凭据
│   ├── stats_service.py           # 统计计算
│   ├── export_service.py          # Excel / 报表导出
│   └── chart_service.py           # 图表 HTML 生成
├── ui/                            # UI 层
│   ├── __init__.py
│   ├── app.py                     # 主窗口 + 路由
│   ├── login_view.py              # 登录界面
│   ├── dashboard_view.py          # 主面板
│   ├── dialogs/                   # 管理对话框
│   │   ├── __init__.py
│   │   ├── material_dialog.py
│   │   ├── worker_dialog.py
│   │   ├── process_dialog.py
│   │   ├── user_dialog.py
│   │   ├── permission_dialog.py
│   │   ├── summary_dialog.py
│   │   └── calendar_dialog.py
│   └── widgets/                   # 可复用组件
│       ├── __init__.py
│       ├── table_widget.py
│       ├── stats_bar.py
│       └── crud_dialog_base.py    # 管理对话框基类
├── utils/                         # 工具
│   ├── __init__.py
│   ├── logger.py                  # 日志
│   ├── error_handler.py           # 全局异常处理
│   └── theme.py                   # 主题/颜色
├── resources/                     # 资源
│   └── echarts.min.js
├── tests/                         # 测试
│   ├── __init__.py
│   ├── test_services/
│   ├── test_models/
│   └── conftest.py
├── requirements.txt
├── Makefile / build.py
└── .github/workflows/
    └── build.yml                  # CI/CD
```

---

## 3. 分层职责

### 3.1 配置层 `config.py`

```python
# 单一配置入口，不再散落在各文件中

class AppConfig:
    # 颜色主题
    BG = '#f0f2f5'
    CARD = '#ffffff'
    PRIMARY = '#1a73e8'
    ACCENT = '#e67e22'
    GREEN = '#27ae60'
    RED = '#e74c3c'
    DARK = '#2c3e50'

    # 路径
    DB_PATH: str
    ECHARTS_PATH: str

    # 权限
    ALL_PERMS = ['record_add','record_delete','record_edit',
                 'material_manage','worker_manage','process_manage',
                 'assignment_manage','chart_view','summary_view',
                 'export_excel','user_manage']
```

### 3.2 数据模型层 `models/`

每个实体对应一个 Repository 类，封装所有 SQL 操作。

```python
# models/database.py
class Database:
    """连接管理，统一配置"""
    _conn: sqlite3.Connection | None = None

    @classmethod
    def get_conn(cls) -> sqlite3.Connection:
        if cls._conn is None:
            cls._conn = sqlite3.connect(Config.DB_PATH)
            cls._conn.row_factory = sqlite3.Row
        return cls._conn

    @classmethod
    def close(cls):
        if cls._conn:
            cls._conn.close()
            cls._conn = None

# models/material.py
class MaterialRepository:
    """物料数据访问"""

    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM materials ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(name: str, price: float = 0) -> int | None:
        """返回新 ID 或 None"""
        conn = Database.get_conn()
        try:
            cur = conn.execute("INSERT INTO materials (name,price) VALUES (?,?)",
                             (name, price))
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise DuplicateError(f"物料 '{name}' 已存在") from e
```

### 3.3 业务逻辑层 `services/`

```python
# services/stats_service.py
class StatsService:
    @staticmethod
    def calculate(start_date: str = None, end_date: str = None,
                  process_filter: int = None, worker_filter: int = None) -> dict:
        """计算统计数据的业务逻辑。"""
        totals = RecordRepository.get_totals(...)
        by_worker = RecordRepository.get_totals_by_worker(...)
        return {'totals': totals, 'by_worker': by_worker, ...}
```

### 3.4 UI 层 `ui/`

```python
# ui/dialogs/crud_dialog_base.py
class CrudDialogBase:
    """Dialog 基类，减少重复代码。"""

    def __init__(self, parent, title, geometry, columns):
        self.top = Toplevel(parent)
        self.top.title(title)
        self.top.geometry(geometry)
        self.columns = columns  # [('name','名称',200), ('price','单价',100)]
        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        self.tree = ttk.Treeview(self.top, ...)
        # ...

    def refresh(self): pass  # override
    def on_add(self): pass   # override
    def on_edit(self): pass  # override
    def on_delete(self): pass # override
```

```python
# ui/dialogs/material_dialog.py
class MaterialDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(parent, '管理物料', '500x400',
                        [('name','名称',200), ('price','单价',100)])

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for m in MaterialRepository.get_all():
            self.tree.insert('', END, values=(m['name'], m['price']))

    def on_add(self):
        name = self.entry_name.get().strip()
        price = float(self.entry_price.get() or 0)
        MaterialRepository.add(name, price)
        self.refresh()
```

### 3.5 日志 `utils/logger.py`

```python
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('prod_sys')
```

---

## 4. 分阶段重构路线图

### 第一阶段：基础设施（1-2 天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1.1 | 新建包结构 `models/` `services/` `ui/` `utils/` | 目录骨架 |
| 1.2 | 提取 `config.py` | 统一配置入口 |
| 1.3 | 建立 `utils/logger.py` | 日志系统 |
| 1.4 | 建立 `utils/error_handler.py` | 全局异常处理 + 弹窗 |
| 1.5 | 建立 `models/database.py` | 连接管理 |

**风险**：此阶段不影响现有功能，风险最低。

### 第二阶段：数据层抽取（2-3 天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 2.1 | 抽取 `models/material.py` | 物料 Repository |
| 2.2 | 抽取 `models/worker.py` | 工人 Repository |
| 2.3 | 抽取 `models/process.py` | 工序 Repository |
| 2.4 | 抽取 `models/record.py` | 记录 + 统计 Repository |
| 2.5 | 抽取 `models/user.py` | 用户 + 权限 Repository |
| 2.6 | 将 `init_db` 拆分到各 Repository 的 `migrate()` | 数据库初始化 |

**验证**：现有 `main.py` 中的全局函数改为调用 Repository 后行为不变。

### 第三阶段：业务逻辑层（2-3 天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 3.1 | `services/auth_service.py` | 登录校验、密码修改、凭据管理 |
| 3.2 | `services/stats_service.py` | 统计计算 |
| 3.3 | `services/export_service.py` | Excel 导出 + 图表 HTML 生成 |
| 3.4 | 为各 Service 编写单元测试 | `tests/test_services/` |

### 第四阶段：UI 层重构（3-5 天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 4.1 | 提取 `ui/widgets/table_widget.py` | 通用表格组件 |
| 4.2 | 提取 `ui/widgets/stats_bar.py` | 统计卡片栏 |
| 4.3 | 提取 `ui/widgets/crud_dialog_base.py` | 管理对话框基类 |
| 4.4 | 按基类重写 5 个管理对话框 | `material_dialog.py` 等 |
| 4.5 | 提取 `ui/login_view.py` | 登录界面 |
| 4.6 | 提取 `ui/dashboard_view.py` | 主面板 + 工具栏 |
| 4.7 | 提取 `ui/dialogs/calendar_dialog.py` | 日历选择器 |
| 4.8 | `ui/app.py` 整合所有 View | 主窗口路由 |

### 第五阶段：构建与 CI（1 天）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 5.1 | `requirements.txt` | 依赖锁定 |
| 5.2 | `Makefile` / `build.py` | 一键打包 |
| 5.3 | GitHub Actions `build.yml` | 自动构建 exe |

---

## 5. 数据流设计（重构后）

```
用户操作 → View (UI)
              │
              ▼
         Service (业务逻辑)
              │
              ▼
         Repository (数据访问)
              │
              ▼
         SQLite (存储)
```

```
登录流程:
LoginView ──→ AuthService.login() ──→ UserRepository.find_by_username()
                │                            │
                ▼                            ▼
           校验密码 ◄────────── 返回用户记录
                │
                ▼
         DashboardView.show(user, perms)

添加记录:
DashboardView ──→ RecordService.add() ──→ WorkerRepository.get_by_id()
                   │                        │
                   │                     ProcessRepository.get_by_id()
                   │                        │
                   ▼                        ▼
            计算工资 ◄────── 获取工人+工序
                   │
                   ▼
             RecordRepository.create()
```

---

## 6. 收益对比

| 指标 | 当前架构 | 重构后 |
|------|----------|--------|
| 文件数 | 1 | ~30 |
| 总代码量 | ~1071 行 | ~1500 行（含空行/注释） |
| 单个文件最大 | 1071 行 | <200 行 |
| 可测试代码 | 0% | >80% |
| 新增一个管理对话框 | 复制粘贴 80 行 | 继承基类 + 30 行 |
| 切换数据库 | 重写全部 SQL | 改 Database 类 |
| 添加日志 | 不可能 | 一行 `logger.info()` |
| 定位 bug | 肉眼排查 | 查看日志文件 |

---

## 7. 不动的内容

以下功能保持原样，只做位置移动，不改逻辑：

- ✅ 所有数据库表结构
- ✅ 密码哈希算法（PBKDF2-SHA256）
- ✅ 记住密码机制
- ✅ 权限检查逻辑
- ✅ ECharts 图表 HTML 模板
- ✅ Excel 导出格式
- ✅ UI 布局和交互行为

---

## 8. 建议的重构策略

**不要一次性重写。** 建议采用**绞杀者模式（Strangler Fig Pattern）**：

1. **先搭骨架**：建好目录结构、`config.py`、`database.py`、`logger.py`
2. **逐层替换**：从数据层开始，一次替换一个 Repository
3. **并行运行**：新旧代码可以共存，每个 Repository 写好后修改 import 即可
4. **逐个测试**：每替换一个模块，跑一遍对应的功能验证
5. **最后拆 UI**：UI 层依赖最小化后，最后拆分

> ⚠️ **不推荐的策略**：一次性重写全部代码。这会引入大量新 bug，且无法与现有 exe 对照调试。
