"""
生产管理系统 ProductionSystem
"""
import sqlite3, os, sys, webbrowser, tempfile, json, shutil, calendar
import hashlib, secrets, base64
from datetime import date, timedelta
from tkinter import *
from tkinter import ttk, messagebox

# ── 使用新架构模块 ──
from config import DB_PATH, ECHARTS_PATH, LOGIN_CRED_PATH, YEN, ALL_PERMS
from config import BG, CARD, PRIMARY, ACCENT, GREEN, RED, DARK
from utils.auth import hash_password as _hash_pw, verify_password as _verify_pw
from utils.auth import save_credential as _save_cred, load_credential as _load_cred
from utils.auth import clear_credential as _clear_cred

def _rp(rel):
    try: base = sys._MEIPASS
    except: base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

def _set_placeholder(entry, text):
    entry._ph_text = text
    entry.insert(0, text)
    entry.config(fg='#999999')
    def _in(e):
        if entry.get() == entry._ph_text:
            entry.delete(0, END); entry.config(fg='#333333')
    def _out(e):
        if not entry.get().strip():
            entry.insert(0, entry._ph_text); entry.config(fg='#999999')
    entry.bind('<FocusIn>', _in, '+'); entry.bind('<FocusOut>', _out, '+')


# ── Database ──

from models.database import Database
from models.record import RecordRepository
from models.user import UserRepository
from services.material_service import MaterialService
from services.worker_service import WorkerService
from services.process_service import ProcessService
from services.auth_service import AuthService
from services.stats_service import StatsService

init_db = Database.init_db
get_conn = Database.get_conn
get_materials = MaterialService.get_all
add_material = MaterialService.add
update_material = MaterialService.update
delete_material = MaterialService.delete
get_workers = WorkerService.get_all
add_worker = WorkerService.add
delete_worker = WorkerService.delete
get_processes = ProcessService.get_all
add_process = ProcessService.add
delete_process = ProcessService.delete
get_worker_processes = ProcessService.get_worker_processes
assign_worker_process = ProcessService.assign_worker
unassign_worker_process = ProcessService.unassign_worker

# ── 仍在 main.py 中使用的函数 ──
get_users = UserRepository.get_all
get_user_by_worker_id = UserRepository.get_by_worker_id
add_user = UserRepository.add
update_user_pw = UserRepository.update_password
update_user_display = UserRepository.update_profile
delete_user = UserRepository.delete
get_user_perms = UserRepository.get_permissions
set_user_perm = UserRepository.set_permission
update_worker = WorkerService.update
add_record = RecordRepository.add
update_record = RecordRepository.update
delete_record = RecordRepository.delete
get_all_records = RecordRepository.get_all
get_stats = StatsService.get_summary
list_months = RecordRepository.list_months

# ── 服务层 ──
from services.chart_service import _chart_html, gen_report
from services.export_service import export_excel

# ── 基本路径 ──
if getattr(sys, "frozen", False): _BASE = os.path.dirname(sys.executable)
else: _BASE = os.path.dirname(os.path.abspath(__file__))

# ── UI 模块（显式导入确保 PyInstaller 打包）──
from ui.widgets.crud_dialog_base import CrudDialogBase
from ui.dialogs.material_dialog import MaterialDialog
from ui.dialogs.worker_dialog import WorkerDialog
from ui.dialogs.process_dialog import ProcessDialog


class App:
    def __init__(self):
        self.root = Tk()
        self.root.title('生产管理系统')
        self.root.geometry('1200x750')
        self.root.configure(bg=BG)
        self.root.withdraw()
        self.current_user = None
        self.user_perms = {}
        self.dashboard = None
        self._show_login()

    def _show_login(self):
        from ui.login_view import LoginView
        login = LoginView(self.root)
        user = login.show()
        if user:
            self.current_user = user
            self.user_perms = login.get_permissions()
            self.root.deiconify()
            self._show_dashboard()

    def _show_dashboard(self):
        from ui.dashboard_view import DashboardView
        self.dashboard = DashboardView(self.root, self.current_user, self.user_perms,
                                       on_logout=self._logout)

    def _logout(self):
        if messagebox.askyesno('确认', '确定退出登录？'):
            self.dashboard = None
            self.current_user = None
            self.user_perms = {}
            for w in self.root.winfo_children():
                w.destroy()
            self.root.withdraw()
            self._show_login()

if __name__ == '__main__':
    init_db()
    app = App()
    app.root.mainloop()
