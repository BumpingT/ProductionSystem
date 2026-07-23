"""
登录对话框视图
"""
from tkinter import Toplevel, Label, Frame, Entry, Button, Checkbutton, IntVar
from tkinter import messagebox
from config import CARD, PRIMARY, DARK
from services.auth_service import AuthService
from utils.auth import save_credential as _save_cred, load_credential as _load_cred
from utils.auth import clear_credential as _clear_cred
from models.user import UserRepository


class LoginView:
    def __init__(self, root):
        self.root = root
        self.top = None
        self.current_user = None
        self.user_perms = {}
        self._result = None

    def show(self) -> dict | None:
        """显示登录对话框，返回用户信息或 None"""
        self.top = Toplevel(self.root)
        self.top.title('生产管理系统 登录')
        self.top.geometry('340x320')
        self.top.configure(bg=CARD)
        self.top.resizable(False, False)
        self.top.grab_set()

        Label(self.top, text='生产管理系统', font=('Microsoft YaHei', 16, 'bold'),
              bg=CARD, fg=PRIMARY).pack(pady=(24, 4))
        Label(self.top, text='请输入账号密码', font=('Microsoft YaHei', 9),
              bg=CARD, fg='#888').pack(pady=(0, 12))

        f = Frame(self.top, bg=CARD)
        f.pack(padx=24)
        Label(f, text='用户名：', bg=CARD, fg='#555',
              font=('Microsoft YaHei', 10)).pack(anchor='w')
        self.un_entry = Entry(f, width=25, relief='solid',
                              font=('Microsoft YaHei', 10), bd=1)
        self.un_entry.pack(pady=(2, 8))
        Label(f, text='密码：', bg=CARD, fg='#555',
              font=('Microsoft YaHei', 10)).pack(anchor='w')
        self.pw_entry = Entry(f, width=25, relief='solid',
                              font=('Microsoft YaHei', 10), show='*', bd=1)
        self.pw_entry.pack(pady=(2, 6))

        self.cred_var = IntVar()
        rf = Frame(f, bg=CARD)
        rf.pack(fill='x')
        Checkbutton(rf, text='记住密码', variable=self.cred_var,
                    bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        Label(rf, text='默认: admin/admin123', bg=CARD, fg='#999',
              font=('Microsoft YaHei', 8)).pack(side='right')

        Button(f, text='登录', bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 11, 'bold'),
               relief='flat', padx=8, pady=4, cursor='hand2',
               command=self._do_login).pack(fill='x', pady=(8, 0))

        # Load saved credentials
        cred = _load_cred()
        if cred:
            self.un_entry.insert(0, cred.get('u', ''))
            self.pw_entry.insert(0, cred.get('p', ''))
            self.cred_var.set(1)

        self.un_entry.focus()
        self.top.bind('<Return>', lambda e: self._do_login())
        self.root.wait_window(self.top)
        return self._result

    def _do_login(self):
        un = self.un_entry.get().strip()
        pw = self.pw_entry.get()
        if not un or not pw:
            messagebox.showinfo('提示', '请输入用户名和密码')
            return
        # 去掉密码首尾空格，避免用户不小心输入了空格
        pw_stripped = pw.strip()
        if pw != pw_stripped:
            pw = pw_stripped
        user = AuthService.login(un, pw)
        if not user:
            messagebox.showerror('错误', '用户名或密码错误')
            return
        self.current_user = user
        self.user_perms = UserRepository.get_permissions(un)
        if self.cred_var.get():
            _save_cred(un, pw)
        else:
            _clear_cred()
        self._result = user
        self.top.destroy()

    def get_permissions(self) -> dict:
        return self.user_perms
