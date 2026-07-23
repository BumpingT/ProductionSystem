"""
用户管理对话框 — 添加/编辑/删除系统用户
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, LEFT, StringVar
from tkinter import messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY, ROLE_NAMES, ROLE_NAMES_REV
from models.user import UserRepository
from models.worker import WorkerRepository
from utils.logger import logger


class UserDialog:
    """用户管理对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        logger.info('正在创建用户管理对话框')
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
        self.tree = ttk.Treeview(self.top, columns=('username', 'role', 'group', 'worker'),
                                  show='headings', height=10)
        col_defs = [('username', '用户名', 120),
                    ('role', '角色', 80), ('group', '班组', 80), ('worker', '关联工人', 120)]
        for col, text, w in col_defs:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=16, pady=(4, 4))
        
        # ── 添加/编辑区域 ──
        f = Frame(self.top, bg=CARD)
        f.pack(fill='x', padx=16, pady=4)
        
        # 第一行：用户名、密码
        r1 = Frame(f, bg=CARD)
        r1.pack(fill='x', pady=(0, 4))
        Label(r1, text='用户名:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.e_user = Entry(r1, width=12, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_user.pack(side=LEFT, padx=(2, 8))
        
        Label(r1, text='密码:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.e_pw = Entry(r1, width=12, font=('Microsoft YaHei', 11), relief='solid', bd=1, show='*')
        self.e_pw.pack(side=LEFT, padx=(2, 8))
        
        # 第二行：角色、组别、关联工人
        r2 = Frame(f, bg=CARD)
        r2.pack(fill='x')
        Label(r2, text='角色:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.cb_role = ttk.Combobox(r2, values=['生产工人', '组长', '生产部部长', '管理员'],
                                     state='normal', width=12)
        self.cb_role.pack(side=LEFT, padx=(2, 8))
        self.cb_role.set('生产工人')
        
        # ── 关联组别 ──
        self._group_list = []
        try:
            rows = WorkerRepository.get_all()
            group_set = set()
            for w in rows:
                g = w.get('group_name', '').strip()
                if g:
                    group_set.add(g)
            self._group_list = sorted(group_set)
        except Exception as e:
            logger.error(f'获取组别列表失败: {e}')
        gvals = ['(无)'] + self._group_list
        Label(r2, text='班组:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        self.cb_group = ttk.Combobox(r2, values=gvals, width=12)
        self.cb_group.pack(side=LEFT, padx=(2, 8))
        self.cb_group.set('(无)')
        # 根据角色显示/隐藏组别
        self._toggle_group()
        self.cb_role.bind('<<ComboboxSelected>>', lambda e: self._toggle_group())
        
        self._worker_frame = Frame(r2, bg=CARD)
        Label(self._worker_frame, text='关联工人:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        try:
            workers = WorkerRepository.get_all()
            self._worker_list = workers
            wvals = ['(无)'] + [w['name'] for w in workers]
        except Exception as e:
            logger.error(f'获取工人列表失败: {e}')
            self._worker_list = []
            wvals = ['(无)']
        self.cb_worker = ttk.Combobox(self._worker_frame, values=wvals, width=15)
        self.cb_worker.pack(side=LEFT, padx=(2, 4))
        self.cb_worker.set('(无)')
        self._worker_frame.pack(side=LEFT)
        # 选择工人时自动填入组别
        self.cb_worker.bind('<<ComboboxSelected>>', lambda e: self._on_worker_selected())
        
        # 保存完整工人列表
        self._all_workers = self._worker_list[:]
        # 组别变化时过滤工人
        self.cb_group.bind('<<ComboboxSelected>>', lambda e: self._update_worker_list())
        
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
        self.top.wait_window()  # 阻塞直到对话框关闭

    def _save_and_refresh(self):
        """刷新并保持选中行置顶"""
        old = self.tree.selection()
        old_iid = old[0] if old else None
        self.refresh()
        if old_iid and old_iid in self.tree.get_children():
            children = self.tree.get_children()
            idx = list(children).index(old_iid)
            total = len(children)
            if total > 0:
                self.tree.yview_moveto(idx / total if idx / total < 0.9 else 0.9)
            self.tree.selection_set(old_iid)
            self.tree.focus(old_iid)

    def _on_worker_selected(self):
        """选择工人后自动填入组别"""
        idx = self.cb_worker.current()
        if idx > 0 and idx <= len(self._all_workers):
            worker = self._all_workers[idx - 1]
            g = worker.get('group_name', '')
            if g:
                self.cb_group.set(g)

    def _toggle_group(self):
        """组别下拉框始终可用"""
        self.cb_group.config(state='normal')
        # 关联工人仅对生产工人显示
        is_worker = self.cb_role.get() == '生产工人'
        if hasattr(self, '_worker_frame'):
            if is_worker:
                self._worker_frame.pack(side=LEFT)
            else:
                self._worker_frame.pack_forget()
                self.cb_worker.set('(无)')
        self._update_worker_list()

    def _update_worker_list(self):
        """根据组别过滤关联工人列表"""
        if not hasattr(self, 'cb_worker'):
            return
        group_val = self.cb_group.get()
        is_leader = self.cb_role.get() == '组长'
        if is_leader and group_val and group_val != '(无)':
            # 组长：只显示对应组别的工人
            self._worker_list = [w for w in self._all_workers if w.get('group_name', '') == group_val]
        else:
            # 其他角色：显示所有工人
            self._worker_list = self._all_workers[:]
        wvals = ['(无)'] + [w['name'] for w in self._worker_list]
        self.cb_worker.config(values=wvals)
        self.cb_worker.set('(无)')

    def refresh(self):
        """刷新用户列表"""
        logger.info('refresh() 被调用')
        try:
            self.tree.delete(*self.tree.get_children())
            users = UserRepository.get_all()
            logger.info(f'刷新用户列表: {len(users)} 个用户')
            if not users:
                logger.warning('用户列表为空，数据库中可能没有用户')
                self.err_label.config(text='数据库中暂无用户数据')
                return
            for u in users:
                worker_name = ''
                if u.get('worker_id') and u['worker_id'] > 0:
                    for w in self._worker_list:
                        if w['id'] == u['worker_id']:
                            worker_name = w['name']
                            break
                self.tree.insert('', 'end', iid=u['username'],
                               values=(u['username'],
                                       ROLE_NAMES.get(u['role'], u['role']),
                                       u.get('group_name', ''), worker_name))
        except Exception as e:
            logger.error(f'刷新用户列表失败: {e}')
            self.err_label.config(text=f'加载用户失败: {e}')
    
    def _get_selected_user(self):
        """获取当前选中的用户名"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个用户', parent=self.top)
            return None
        return sel[0]
    
    def _on_add(self):
        """添加用户"""
        username = self.e_user.get().strip()
        password = self.e_pw.get().strip()
        display = username  # 显示名不再单独设置
        role_cn = self.cb_role.get()
        # 中文角色名转英文存储（自定义角色直接存储）
        role = ROLE_NAMES_REV.get(role_cn, role_cn)
        widx = self.cb_worker.current()
        worker_id = 0
        if widx > 0 and widx <= len(self._worker_list):
            worker_id = self._worker_list[widx - 1]['id']
        
        # 获取组别
        group_val = self.cb_group.get()
        group_name = group_val if group_val != '(无)' else ''
        
        if not username or not password:
            self.err_label.config(text='用户名和密码不能为空')
            return
        if len(password) < 4:
            self.err_label.config(text='密码至少4位')
            return
        
        if UserRepository.add(username, password, display, role, worker_id, group_name):
            # 如果有关联工人且选了组别，同步更新工人的组别
            if worker_id and group_name:
                for w in self._all_workers:
                    if w['id'] == worker_id:
                        WorkerRepository.update(worker_id, w['name'], group_name)
                        break
            # 如果是组长，自动关联本组所有工人
            if role == 'leader' and group_name:
                group_workers = [w for w in WorkerRepository.get_all() if w.get('group_name') == group_name]
                UserRepository.set_leader_workers(username, [w['id'] for w in group_workers])
            self.err_label.config(text='', fg=RED)
            self.e_user.delete(0, END)
            self.e_pw.delete(0, END)
            self.cb_role.set('生产工人')
            self.cb_worker.set('(无)')
            self.cb_group.set('(无)')
            self._toggle_group()
            self.refresh()
            messagebox.showinfo('成功', f'用户 "{username}" 已添加', parent=self.top)
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
            messagebox.showerror('错误', '用户不存在', parent=self.top)
            return
        
        # 弹出编辑对话框
        top = Toplevel(self.top)
        top.title(f'编辑用户 - {un}')
        top.geometry('360x260')
        top.configure(bg=CARD)
        top.transient(self.top)
        top.grab_set()
        top.focus_force()
        top.lift()
        
        Label(top, text=f'编辑用户: {un}', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 8))
        
        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        
        # 用户名
        Label(f, text='用户名:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=W, pady=3)
        e_un = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_un.insert(0, un)
        e_un.grid(row=0, column=1, pady=3, padx=(4, 0))
        
        Label(f, text='角色:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=W, pady=3)
        cb_r = ttk.Combobox(f, values=['生产工人', '组长', '生产部部长', '管理员'], state='normal', width=18)
        role_cn = ROLE_NAMES.get(user.get('role', 'worker'), '生产工人')
        cb_r.set(role_cn)
        cb_r.grid(row=1, column=1, pady=3, padx=(4, 0))
        
        # 组别（仅组长）
        group_list = []
        try:
            rows = WorkerRepository.get_all()
            group_set = set()
            for w in rows:
                g = w.get('group_name', '').strip()
                if g:
                    group_set.add(g)
            group_list = sorted(group_set)
        except Exception:
            pass
        gvals = ['(无)'] + group_list
        Label(f, text='班组:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky=W, pady=3)
        cb_g = ttk.Combobox(f, values=gvals, width=18)
        cur_group = user.get('group_name', '')
        cb_g.set(cur_group if cur_group else '(无)')
        cb_g.grid(row=2, column=1, pady=3, padx=(4, 0))
        
        # 关联工人
        worker_frame = Frame(f, bg=CARD)
        worker_frame.grid(row=3, column=0, columnspan=2, sticky=W, pady=1)
        Label(worker_frame, text='关联工人:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        all_workers = WorkerRepository.get_all()
        worker_names = ['(无)'] + [w['name'] for w in all_workers]
        cb_w = ttk.Combobox(worker_frame, values=worker_names, width=18)
        cur_wid = user.get('worker_id', 0)
        if cur_wid:
            for w in all_workers:
                if w['id'] == cur_wid:
                    cb_w.set(w['name'])
                    break
        if not cur_wid or not cb_w.get():
            cb_w.set('(无)')
        cb_w.pack(side=LEFT, padx=(4, 0))
        
        Label(f, text='新密码(留空不改):', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=4, column=0, sticky=W, pady=3)
        e_pw = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        e_pw.grid(row=4, column=1, pady=3, padx=(4, 0))
        
        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack(pady=(4, 0))
        
        def do_save():
            new_un = e_un.get().strip()
            if not new_un:
                err.config(text='用户名不能为空')
                return
            rl_cn = cb_r.get()
            role_map = ROLE_NAMES_REV
            rl = role_map.get(rl_cn, rl_cn)
            npw = e_pw.get().strip()
            gv = cb_g.get()
            gp = gv if gv != '(无)' else ''
            # 获取关联工人ID
            new_wid = 0
            w_idx = cb_w.current()
            if w_idx > 0 and w_idx <= len(all_workers):
                new_wid = all_workers[w_idx - 1]['id']
            # 如果用户名变了，先重命名
            if new_un != un:
                if not UserRepository.rename(un, new_un):
                    err.config(text='用户名已存在或重命名失败')
                    return
            UserRepository.update_profile(new_un, new_un, rl, new_wid, gp)
            # 如果有关联工人且改了组别，同步更新工人的组别
            if new_wid and gp:
                for w in WorkerRepository.get_all():
                    if w['id'] == new_wid:
                        WorkerRepository.update(new_wid, w['name'], gp)
                        break
            # 如果是组长，更新管辖工人关联
            if rl == 'leader' and gp:
                group_workers = [w for w in WorkerRepository.get_all() if w.get('group_name') == gp]
                UserRepository.set_leader_workers(new_un, [w['id'] for w in group_workers])
            elif rl != 'leader':
                UserRepository.set_leader_workers(new_un, [])
            if npw:
                if len(npw) < 4:
                    err.config(text='密码至少4位')
                    return
                UserRepository.update_password(new_un, npw)
            top.destroy()
            self._save_and_refresh()
            messagebox.showinfo('成功', '用户信息已更新', parent=self.top)
        
        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2', command=do_save).pack(pady=(8, 4))
    
    def _on_delete(self):
        """删除选中的用户"""
        un = self._get_selected_user()
        if not un:
            return
        if un == 'admin':
            messagebox.showinfo('提示', '不能删除管理员账号', parent=self.top)
            return
        if messagebox.askyesno('确认', f'确定删除用户 "{un}"？', parent=self.top):
            if UserRepository.delete(un):
                self._save_and_refresh()
                messagebox.showinfo('成功', f'用户 "{un}" 已删除', parent=self.top)
            else:
                messagebox.showerror('错误', '删除失败', parent=self.top)
