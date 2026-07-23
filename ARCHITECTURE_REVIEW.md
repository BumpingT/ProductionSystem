# 生产管理系统 — 架构审查报告

> 审查日期: 2026-07 | 基于 v45 版本

---

## 一、总体评价

项目整体功能完整、运行稳定，分层架构方向正确（models → services → ui），但存在若干**架构腐蚀**现象，随着 45 个版本的迭代，代码质量和架构一致性出现明显退化。

---

## 二、严重问题（必须修复）

### 🔴 问题1：main.py 全局函数别名破坏分层

**现象**：main.py 从 models/services 导入所有函数并重定义为全局函数：

```python
# main.py 中
get_materials = MaterialService.get_all
get_workers = WorkerService.get_all
add_record = RecordRepository.add
# ... 20+ 个别名
```

UI 层（dashboard_view.py）大量直接引用这些全局函数，**绕过了 Service 层和模块边界**。

**危害**：
- 分层架构名存实亡
- 循环依赖风险（ui → main → models）
- 代码难以调试和测试
- 新人难以理解调用链

### 🔴 问题2：DashboardView 过于庞大（~1250行）

**现象**：`ui/dashboard_view.py` 包含了：

| 职责 | 行数 | 说明 |
|------|------|------|
| 主界面构建 | ~100 | 工具栏、筛选栏、表单、表格、状态栏 |
| 记录 CRUD | ~80 | 添加、删除、刷新 |
| 编辑记录对话框 | ~200 | 内联 Toplevel 创建 |
| 修改密码对话框 | ~70 | 内联 Toplevel |
| 权限管理对话框 | ~80 | 内联 Canvas+Checkbutton |
| 月度汇总对话框 | ~100 | 含表格+导出+图表 |
| 汇总查询对话框 | ~100 | 含日期筛选+表格+导出 |
| 日历控件 | ~80 | 完整月历实现 |
| 筛选逻辑 | ~80 | 直接拼接 SQL |
| 合计 | **~1250** | |

**危害**：
- 严重违反单一职责原则
- 难以维护、测试、扩展
- 一个小修改可能影响全局

### 🔴 问题3：业务逻辑散落在 UI 层

**现象**：
- `_apply_filter()` 方法**直接拼接 SQL 字符串**（第700-770行）
- `_edit_record()` 中处理复杂的权限验证逻辑
- 相同的权限过滤代码在 `RecordRepository.get_all()`、`get_stats()`、`_apply_filter()` 中**重复 3 次**

**危害**：
- 数据库访问逻辑散落在 UI 层，更换数据库需要改动 UI
- 权限策略变更需要修改多个文件
- 无法通过单元测试覆盖 UI 层中的业务逻辑

---

## 三、中等问题（建议修复）

### 🟡 问题4：Service 层形同虚设

MaterialService、WorkerService、ProcessService 只是简单的"透传"层：
```python
class MaterialService:
    @staticmethod
    def get_all():
        return MaterialRepository.get_all()  # 纯透传
```

UI 层经常直接调用 Repository 跳过 Service 层。

### 🟡 问题5：ProcessDialog 未继承 CrudDialogBase

MaterialDialog、WorkerDialog 继承自 CrudDialogBase，但 ProcessDialog 自行实现，造成风格不一致和代码重复（placeholder、_save_and_refresh 等）。

### 🟡 问题6：导入方式不统一

- 文件顶部 import 与函数内部 import 混用
- 存在大量函数内 `from xxx import yyy as ZZ` 的写法
- 相对导入和绝对导入混用

### 🟡 问题7：测试覆盖严重不足

- 只有 19 项测试（auth 12 + stats 7）
- 占 90% 的 UI 层代码零测试覆盖
- Service 层零测试覆盖
- Repository 层零测试覆盖

---

## 四、优化方案

### 优先级 P0（立即执行）

| 优化 | 说明 | 改动量 |
|------|------|--------|
| 拆分内联对话框 | 从 DashboardView 拆出 EditRecordDialog、ChangePasswordDialog、PermissionDialog | ~300行新增 |
| 重构 main.py | 移除全局函数别名，改为按需导入 | ~50行修改 |
| 增强 Service 层 | 将权限过滤逻辑移到 Service 层 | ~100行修改 |

### 优先级 P1（后续迭代）

| 优化 | 说明 |
|------|------|
| 统一 ProcessDialog 继承 CrudDialogBase | 减少重复代码 |
| 添加 Service 层单元测试 | 覆盖核心业务逻辑 |
| 统一导入规范 | 消除函数内 import |

---

## 五、优化执行结果

### ✅ 已完成的架构优化

| 优化项 | 状态 | 涉及文件 | 说明 |
|--------|------|---------|------|
| main.py 移除全局函数别名 | ✅ 完成 | `main.py` | 从 136 行精简为 58 行，消除 20+ 个别名 |
| 拆分编辑记录对话框 | ✅ 完成 | `ui/dialogs/edit_record_dialog.py` | 从 DashboardView 移出 ~200 行内联代码 |
| 拆分修改密码对话框 | ✅ 完成 | `ui/dialogs/change_password_dialog.py` | 从 DashboardView 移出 ~70 行内联代码 |
| 拆分权限管理对话框 | ✅ 完成 | `ui/dialogs/permission_dialog.py` | 从 DashboardView 移出 ~80 行内联代码 |
| 创建 PermissionService | ✅ 完成 | `services/permission_service.py` | 集中数据权限过滤逻辑 |
| RecordRepository 使用 PermissionService | ✅ 完成 | `models/record.py` | 消除 get_all/get_stats 中的重复权限判断 |
| DashboardView._apply_filter 使用 PermissionService | ✅ 完成 | `ui/dashboard_view.py` | 消除 UI 层重复的权限 SQL |

### 📊 量化效果

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| `main.py` 行数 | 136 行 | 58 行 | **-57%** |
| `dashboard_view.py` 行数 | ~1250 行 | ~1050 行 | **-16%** |
| 独立对话框类数量 | 4 个 | 7 个 | **+75%** |
| 权限过滤逻辑重复次数 | 3 处 | 1 处（PermissionService） | **-67%** |
| 全局函数别名 | 20+ 个 | 0 个 | **-100%** |

### 📋 待改进项（P1 后续迭代）

| 待改进 | 说明 | 预估工时 |
|--------|------|---------|
| ProcessDialog 继承 CrudDialogBase | 统一风格，消除占位符等重复代码 | 0.5d |
| Service 层单元测试 | 覆盖 MaterialService / WorkerService / PermissionService | 1d |
| UI 层测试 | 添加对话框和主视图的集成测试 | 2d |
| 统一导入规范 | 消除函数内 `import`，文件顶部统一导入 | 0.5d |
