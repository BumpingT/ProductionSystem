"""
修改密码对话框 — 从 DashboardView 拆分为独立组件
"""
from tkinter import Toplevel, Label, Frame, Button, Entry
from tkinter import messagebox
from config import CARD, DARK, ACCENT, RED
from models.user import UserRepository
from utils.auth import verify_password


class ChangePasswordDialog:
    """修改当前用户密码"""

    def __init__(self, parent_root, current_user):
        self.root = parent_root
        self.current_user = current_user
        self._build()

    def _build(self):
        un = self.current_user['username'] if self.current_user else ''
        if not un:
            return

        cp = Toplevel(self.root)
        cp.title('修改密码')
        cp.geometry('320x230')
        cp.configure(bg=CARD)
        cp.resizable(False, False)
        cp.grab_set()
        cp.transient(self.root)
        xp = self.root.winfo_x() + self.root.winfo_width() // 2 - 160
        yp = self.root.winfo_y() + self.root.winfo_height() // 2 - 115
        cp.geometry(f'+{xp}+{yp}')

        Label(cp, text='修改密码', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(12, 10))
        ff = Frame(cp, bg=CARD)
        ff.pack(padx=24)
        Label(ff, text='用户名：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=0, column=0, sticky='w', pady=3)
        eu = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        eu.insert(0, un)
        eu.config(state='readonly')
        eu.grid(row=0, column=1, pady=3)
        Label(ff, text='旧密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=1, column=0, sticky='w', pady=3)
        eo = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        eo.grid(row=1, column=1, pady=3)
        Label(ff, text='新密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=2, column=0, sticky='w', pady=3)
        en = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        en.grid(row=2, column=1, pady=3)
        Label(ff, text='确认密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=3, column=0, sticky='w', pady=3)
        ec = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        ec.grid(row=3, column=1, pady=3)
        err2 = Label(cp, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err2.pack(pady=(4, 0))

        def do_change():
            opw = eo.get().strip()
            npw = en.get().strip()
            cpw = ec.get().strip()
            if not opw or not npw:
                err2.config(text='请填写完整')
                return
            if npw != cpw:
                err2.config(text='两次新密码不一致')
                return
            if len(npw) < 4:
                err2.config(text='新密码至少4位')
                return
            user = UserRepository.get_by_username(un)
            if not user:
                err2.config(text='用户不存在')
                return
            if not verify_password(opw, user['password_hash']):
                err2.config(text='旧密码错误')
                return
            if verify_password(npw, user['password_hash']):
                err2.config(text='新密码不能与旧密码相同')
                return
            UserRepository.update_password(un, npw)
            from utils.auth import clear_credential
            clear_credential()
            messagebox.showinfo('成功', '密码修改成功', parent=cp)
            cp.destroy()

        Button(cp, text='确认修改', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=20, pady=2, cursor='hand2',
               command=do_change).pack(pady=(6, 0))
        eo.focus()
