"""Bug 验证脚本"""
import sys, os, tempfile
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import config
test_db = os.path.join(tempfile.gettempdir(), 'bug_test.db')
config.DB_PATH = test_db
if os.path.exists(test_db):
    os.remove(test_db)

from models.database import Database
Database._conn = None
Database.init_db()

print("=" * 60)
print("Bug 验证报告")
print("=" * 60)

# ---- Bug 1: 空名称物料 ----
from models.material import MaterialRepository
before = len(MaterialRepository.get_all())
r1 = MaterialRepository.add('', 10)
after = len(MaterialRepository.get_all())
if r1 and after > before:
    print(f"BUG 1 确认: 空字符串物料名被添加成功! ({r1})")
    conn = Database.get_conn()
    conn.execute("DELETE FROM materials WHERE name=''")
    conn.commit()
else:
    print("OK 1: 空物料名被拒绝")

# ---- Bug 2: 空名称工人 ----
from models.worker import WorkerRepository
before = len(WorkerRepository.get_all())
r2 = WorkerRepository.add('', 'test')
after = len(WorkerRepository.get_all())
if r2 and after > before:
    print(f"BUG 2 确认: 空字符串工人名被添加成功! ({r2})")
    conn = Database.get_conn()
    conn.execute("DELETE FROM workers WHERE name=''")
    conn.commit()
else:
    print("OK 2: 空工人名被拒绝")

# ---- Bug 3: 空名称工序 ----
from models.process import ProcessRepository
before = len(ProcessRepository.get_all())
r3 = ProcessRepository.add('A-1001', '', 5.0)
after = len(ProcessRepository.get_all())
if r3 and after > before:
    print(f"BUG 3 确认: 空字符串工序名被添加成功! ({r3})")
    conn = Database.get_conn()
    conn.execute("DELETE FROM processes WHERE process_name=''")
    conn.commit()
else:
    print("OK 3: 空工序名被拒绝")

# ---- Bug 4: RR2 作用域 ----
print()
print("BUG 4: _edit_record 中 RR2 作用域问题")
print("  文件: ui/dashboard_view.py 约 361-386 行")
print("  问题: role=='worker' 分支内导入 RR2,")
print("        但 role=='leader' 分支也使用 RR2")
print("        若 leader 编辑记录, RR2 未定义导致 NameError")
print("  严重性: 高 - 组长编辑记录功能不可用")

# ---- Bug 5: 统计标签未更新 ----
print()
print("BUG 5: _refresh_table 统计标签未更新")
print("  文件: ui/dashboard_view.py _refresh_table() 约 659-662 行")
print("  问题: 方法计算了 stats 数据但未更新 self._stat_labels")
print("  代码: stats = RR.get_stats(...)")
print("        t = stats.get('totals', {})  # 未使用!")
print("  影响: 统计卡片始终显示初始值 0")
print("        仅当点击筛选栏的「查询」按钮后才更新")

# ---- Bug 6: Enter键绑定泄漏 ----
print()
print("BUG 6: login_view Enter键绑定泄漏")
print("  文件: ui/login_view.py 第 69 行")
print("  代码: self.root.bind('<Return>', lambda e: self._do_login())")
print("  问题: 绑定在 root 窗口上, 登录后未解绑")
print("  影响: 在主界面按 Enter 可能触发已销毁对象的登录方法")

# ---- Bug 7: 物料编辑使用 simpledialog 而非 tkinter 对话框 ----
print()
print("BUG 7: 物料编辑使用 simpledialog")
print("  文件: ui/dialogs/material_dialog.py on_edit() 约 82 行")
print("  代码: from tkinter.simpledialog import askstring")
print("  问题: askstring 界面风格与整体UI不一致")
print("  严重性: 低 - 功能正常, 仅外观不一致")

Database.close()
if os.path.exists(test_db):
    try:
        os.remove(test_db)
    except:
        pass

print()
print("=" * 60)
print("验证完成")
print("=" * 60)
