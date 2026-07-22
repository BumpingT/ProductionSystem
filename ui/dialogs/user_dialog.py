"""
用户管理对话框 — 添加/编辑/删除系统用户
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, StringVar
from tkinter import messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from models.user import UserRepository
from models.worker import WorkerRepository


class UserDialog:
    """用户管理对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title('用户管理')
        self.top.geometry('700x520')
        self.top.configure(bg=CARD)
        self.top.grab_set()
        
        Label(self.top, text='用户管理', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))
        Label(self.top, text='添加新用户或编辑/删除已有用户', font=('Microsoft YaHei', 9),
              bg=CARD, fg='#888').pack(anchor=W, padx=16)
        
        # ── 用户列表 ──
        self.tree = ttk.Treeview(self.top, columns=('username', 'display', 'role', 'worker'),
                                  show='headings', height=10)
        col_defs = [('username', '用户名', 120), ('display', '显示名', 120),
                    ('role', '角色', 80), ('worker', '关联工人', 120)]
        for col, text, w in col_defs:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w)
        self.tree.pack(fill='both', expand=True, padx=16, pady=(4, 4))
        
        # ── 添加/编辑区域 ──
        f = Frame(self.top, bg=CARD)
        f.pack(fill='x', padx=16, pady=4)
        
        Label(f, text='用户名:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.e_user = Entry(f, width=12, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_user.pack(side=LEFT, padx=(2, 8))
        
        Label(f, text='密码:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.e_pw = Entry(f, width=12, font=('Microsoft YaHei', 11), relief='solid', bd=1, show='*')
        self.e_pw.pack(side=LEFT, padx=(2, 8))
        
        Label(f, text='显示名:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.e_dn = Entry(f, width=10, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_dn.pack(side=LEFT, padx=(2, 8))
        
        Label(f, text='角色:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.cb_role = ttk.Combobox(f, values=['worker', 'leader', 'admin'],
                                     state='readonly', width=8)
        self.cb_role.pack(side=LEFT, padx=(2, 8))
        self.cb_role.set('worker')
        
        Label(f, text='关联工人:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        workers = WorkerRepository.get_all()
        self._worker_list = workers
        wvals = ['(无)'] + [w['name'] for w in workers]
        self.cb_worker = ttk.Combobox(f, values=wvals, state='readonly', width=10)
        self.cb_worker.pack(side=LEFT, padx=(2, 4))
        self.cb_worker.set('(无)')
        
        # ── 按钮 ──
        btn_f = Frame(self.top, bg=CARD)
        btn_f.pack(fill='x', padx=16, pady=6)
        Button(btn_f, text='添加用户', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2', command=self._on_add).pack(side=LEFT, padx=(0, 6))
        Button(btn_f, text='编辑用户', bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2', command=self._on_edit).pack(side=LEFT, padx=(0, 6))
        Button(btn_f, text='删除用户', bg=RED, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2', command=self._on_delete).pack(side=LEFT, padx=(0, 6))
        
        self.err_label = Label(self.top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        self.err_label.pack()
        
        self.refresh()
    
    def refresh(self):
        """刷新用户列表"""
        self.tree.delete(*self.tree.get_children())
        for u in UserRepository.get_all():
            worker_name = ''
            if u.get('worker_id') and u['worker_id'] > 0:
                for w in self._worker_list:
                    if w['id'] == u['worker_id']:
                        worker_name = w['name']
                        break
            self.tree.insert('', 'end', iid=u['username'],
                           values=(u['username'], u['display_name'], u['role'], worker_name))
    
    def _get_selected_user(self):
        """获取当前选中的用户名"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个用户')
            return None
        return sel[0]
    
    def _on_add(self):
        """添加用户"""
        username = self.e_user.get().strip()
        password = self.e_pw.get()
        display = self.e_dn.get().strip() or username
        role = self.cb_role.get()
        widx = self.cb_worker.current()
        worker_id = 0
        if widx > 0 and widx <= len(self._worker_list):
            worker_id = self._worker_list[widx - 1]['id']
        
        if not username or not password:
            self.err_label.config(text='用户名和密码不能为空')
            return
        if len(password) < 4:
            self.err_label.config(text='密码至少4位')
            return
        
        if UserRepository.add(username, password, display, role, worker_id):
            self.err_label.config(text='', fg=RED)
            self.e_user.delete(0, END)
            self.e_pw.delete(0, END)
            self.e_dn.delete(0, END)
            self.cb_role.set('worker')
            self.cb_worker.set('(无)')
            self.refresh()
            messagebox.showinfo('成功', f'用户 "{username}" 已添加')
        else:
            self.err_label.config(text='添加失败，用户名可能已存在')
    
    def _on_edit(self):
        """编辑选中的用户"""
        un = self._get_selected_user()
        if not un:
            return
        if un == 'admin':
            # admin 用户可以编辑自己的显示名和密码，但不能改角色
            pass
        
        user = UserRepository.get_by_username(un)
        if not user:
            messagebox.showerror('错误', '用户不存在')
            return
        
        # 弹出编辑对话框
        top = Toplevel(self.top)
        top.title(f'编辑用户 - {un}')
        top.geometry('360x280')
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(self.top)
        
        Label(top, text=f'编辑用户: {un}', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 8))
        
        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        
        Label(f, text='显示名:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=W, pady=3)
        e_dn = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_dn.insert(0, user.get('display_name', ''))
        e_dn.grid(row=0, column=1, pady=3, padx=(4, 0))
        
        Label(f, text='角色:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=W, pady=3)
        cb_r = ttk.Combobox(f, values=['worker', 'leader', 'admin'], state='readonly', width=18)
        cb_r.set(user.get('role', 'worker'))
        cb_r.grid(row=1, column=1, pady=3, padx=(4, 0))
        
        Label(f, text='新密码(留空不改):', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky=W, pady=3)
        e_pw = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        e_pw.grid(row=2, column=1, pady=3, padx=(4, 0))
        
        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack(pady=(4, 0))
        
        def do_save():
            dn = e_dn.get().strip()
            rl = cb_r.get()
            npw = e_pw.get()
            if not dn:
                err.config(text='显示名不能为空')
                return
            UserRepository.update_profile(un, dn, rl, user.get('worker_id', 0))
            if npw:
                if len(npw) < 4:
                    err.config(text='密码至少4位')
                    return
                UserRepository.update_password(un, npw)
            top.destroy()
            self.refresh()
            messagebox.showinfo('成功', '用户信息已更新')
        
        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2', command=do_save).pack(pady=(8, 4))
    
    def _on_delete(self):
        """删除选中的用户"""
        un = self._get_selected_user()
        if not un:
            return
        if un == 'admin':
            messagebox.showinfo('提示', '不能删除管理员账号')
            return
        if messagebox.askyesno('确认', f'确定删除用户 "{un}"？'):
            if UserRepository.delete(un):
                self.refresh()
                messagebox.showinfo('成功', f'用户 "{un}" 已删除')
            else:
                messagebox.showerror('错误', '删除失败')
