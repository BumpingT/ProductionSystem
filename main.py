"""
生产管理系统 ProductionSystem
"""
import os, sys

from config import DB_PATH
from models.database import Database


def _get_base():
    """获取应用根目录（兼容 PyInstaller 打包）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ── 导出给 PyInstaller 钩子和外部脚本使用 ──
_BASE = _get_base()
init_db = Database.init_db


class App:
    def __init__(self):
        from tkinter import Tk
        self.root = Tk()
        self.root.title('生产管理系统')
        self.root.geometry('1200x750')
        from config import BG
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
        from tkinter import messagebox
        if messagebox.askyesno('确认', '确定退出登录？'):
            self.dashboard = None
            self.current_user = None
            self.user_perms = {}
            for w in self.root.winfo_children():
                w.destroy()
            self.root.withdraw()
            self._show_login()


if __name__ == '__main__':
    from utils.error_handler import setup_global_handler
    setup_global_handler()
    init_db()
    app = App()
    app.root.mainloop()
