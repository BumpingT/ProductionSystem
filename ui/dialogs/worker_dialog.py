"""
工人管理对话框 — 树形结构（班组→工人），班组下拉选择
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from services.worker_service import WorkerService


class WorkerDialog:
    def __init__(self, parent, user=None):
        self.parent = parent
        self._user = user
        self.top = Toplevel(parent)
        self.top.title('管理工人')
        self.top.geometry('620x550')
        self.top.configure(bg=CARD)
        self.top.grab_set()

        Label(self.top, text='班组 · 工人列表（树形展开）', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))

        # ── 树形列表 ──
        self.tree = ttk.Treeview(self.top, columns=('info',), show='tree', height=12)
        self.tree.heading('#0', text='班组 / 工人')
        self.tree.column('#0', width=380)
        self.tree.pack(fill='both', expand=True, padx=16)

        # ── 添加工人区域 ──
        add_frame = Frame(self.top, bg=CARD, highlightbackground='#ddd', highlightthickness=1)
        add_frame.pack(fill='x', padx=16, pady=(6, 2))

        Label(add_frame, text='添加工人', font=('Microsoft YaHei', 10, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=8, pady=(4, 2))

        row1 = Frame(add_frame, bg=CARD)
        row1.pack(fill='x', padx=8, pady=(0, 4))

        Label(row1, text='姓名:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        self.e_name = ttk.Combobox(row1, width=14, font=('Microsoft YaHei', 11))
        self.e_name.pack(side='left', padx=(4, 8))
        # 姓名下拉搜索
        self._refresh_worker_names()
        self.e_name.bind('<KeyRelease>', self._on_worker_name_search)

        Label(row1, text='班组:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        self.cb_group = ttk.Combobox(row1, width=12,
                                      font=('Microsoft YaHei', 10))
        self.cb_group.pack(side='left', padx=(4, 8))

        btn_f1 = Frame(row1, bg=CARD)
        btn_f1.pack(side='left')
        Button(btn_f1, text='添加工人', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2', command=self._on_add_worker).pack(side='left')
        Button(btn_f1, text='编辑工人', bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2', command=self._on_edit_worker).pack(side='left', padx=(4, 0))
        Button(btn_f1, text='删除工人', bg=RED, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2', command=self._on_delete_worker).pack(side='left', padx=(4, 0))

        # ── 管理班组区域 ──
        grp_frame = Frame(self.top, bg=CARD, highlightbackground='#ddd', highlightthickness=1)
        grp_frame.pack(fill='x', padx=16, pady=(2, 8))

        Label(grp_frame, text='管理班组', font=('Microsoft YaHei', 10, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=8, pady=(4, 2))

        row2 = Frame(grp_frame, bg=CARD)
        row2.pack(fill='x', padx=8, pady=(0, 4))

        Label(row2, text='班组名:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        self.e_group = Entry(row2, width=14, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_group.pack(side='left', padx=(4, 8))

        btn_f2 = Frame(row2, bg=CARD)
        btn_f2.pack(side='left')
        Button(btn_f2, text='添加班组', bg=GREEN, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2', command=self._on_add_group).pack(side='left')
        Button(btn_f2, text='删除班组', bg=RED, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2', command=self._on_delete_group).pack(side='left', padx=(4, 0))

        self.refresh()

    def refresh(self):
        """刷新树形列表和班组下拉"""
        self.tree.delete(*self.tree.get_children())
        all_w = WorkerService.get_all()

        # 按班组分组
        groups = WorkerService.get_groups()
        group_workers = {g: [] for g in groups}
        for w in all_w:
            g = w['group_name'] or '(未分组)'
            if g in group_workers:
                group_workers[g].append(w)
            else:
                group_workers[g] = [w]

        for g in groups:
            gid = f'group_{g}'
            workers = group_workers.get(g, [])
            count = len(workers)
            self.tree.insert('', 'end', iid=gid, text=f'  📁 {g}  ({count}人)', open=True)
            for w in workers:
                self.tree.insert(gid, 'end', iid=str(w['id']),
                                text=f'    👤 {w["name"]}')

        # 刷新班组下拉
        self.cb_group['values'] = groups
        if groups:
            self.cb_group.set(groups[0])

    def _get_selected_worker(self):
        """获取选中的工人节点(wid)和值"""
        sel = self.tree.selection()
        if not sel:
            return None, None
        item = sel[0]
        # 如果是班组节点（以 group_ 开头）
        if item.startswith('group_'):
            return None, None
        values = self.tree.item(item, 'text').strip()
        # 提取姓名（去掉图标前缀）
        name = values.replace('👤', '').strip()
        try:
            wid = int(item)
        except ValueError:
            return None, None
        return wid, name

    def _refresh_worker_names(self):
        """刷新工人姓名下拉列表"""
        from services.worker_service import WorkerService as WS
        names = sorted(set(w['name'] for w in WS.get_all()))
        self._all_worker_names = names
        self.e_name['values'] = names

    def _on_worker_name_search(self, ev):
        """姓名下拉输入关键字过滤"""
        kw = self.e_name.get()
        cur = kw
        names = getattr(self, '_all_worker_names', [])
        if kw.strip():
            filtered = [n for n in names if kw.lower() in n.lower()]
            self.e_name['values'] = filtered
        else:
            self.e_name['values'] = names
        if cur != self.e_name.get():
            self.e_name.set(cur)

    def _on_add_worker(self):
        name = self.e_name.get().strip()
        group = self.cb_group.get()
        if not name:
            messagebox.showinfo('提示', '请输入工人姓名', parent=self.top)
            return
        if not group:
            messagebox.showinfo('提示', '请选择班组', parent=self.top)
            return
        if WorkerService.add(name, group):
            self.e_name.set('')
            self.refresh()
        else:
            messagebox.showinfo('提示', '工人已存在', parent=self.top)

    def _on_edit_worker(self):
        wid, cur_name = self._get_selected_worker()
        if wid is None:
            messagebox.showinfo('提示', '请先选择一个工人', parent=self.top)
            return

        # 获取当前工人信息
        from models.worker import WorkerRepository
        all_w = WorkerRepository.get_all()
        worker = next((w for w in all_w if w['id'] == wid), None)
        if not worker:
            return

        top = Toplevel(self.top)
        top.title('编辑工人')
        top.geometry('320x180')
        top.configure(bg=CARD)
        top.transient(self.top)
        top.grab_set()
        top.focus_force()
        top.lift()

        Label(top, text='修改工人信息', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        Label(f, text='姓名:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky='w', pady=3)
        e_name = ttk.Combobox(f, values=worker_names, width=18, font=('Microsoft YaHei', 10))
        e_name.insert(0, worker['name'])
        e_name.grid(row=0, column=1, pady=3, padx=(4, 0))
        Label(f, text='班组:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky='w', pady=3)
        groups = WorkerService.get_groups()
        cb_grp = ttk.Combobox(f, values=groups, width=16)
        cb_grp.set(worker['group_name'] if worker['group_name'] in groups else (groups[0] if groups else ''))
        cb_grp.grid(row=1, column=1, pady=3, padx=(4, 0))

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack()

        def do_save():
            nn = e_name.get().strip()
            ng = cb_grp.get()
            if not nn:
                err.config(text='姓名不能为空')
                return
            WorkerService.update(wid, nn, ng)
            top.destroy()
            self.refresh()
            messagebox.showinfo('成功', '工人信息已更新', parent=self.top)

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete_worker(self):
        wid, name = self._get_selected_worker()
        if wid is None:
            messagebox.showinfo('提示', '请先选择一个工人', parent=self.top)
            return
        if messagebox.askyesno('确认', f'删除工人 "{name}"？', parent=self.top):
            WorkerService.delete(wid)
            self.refresh()

    def _on_add_group(self):
        gname = self.e_group.get().strip()
        if not gname:
            messagebox.showinfo('提示', '请输入班组名称', parent=self.top)
            return
        if WorkerService.add_group(gname):
            self.e_group.delete(0, END)
            self.refresh()
        else:
            messagebox.showinfo('提示', '班组已存在', parent=self.top)

    def _on_delete_group(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个班组', parent=self.top)
            return
        item = sel[0]
        if not item.startswith('group_'):
            messagebox.showinfo('提示', '请选择班组节点（而非工人节点）', parent=self.top)
            return
        gname = item.replace('group_', '')
        # 获取组内工人数
        children = self.tree.get_children(item)
        count = len(children)
        if messagebox.askyesno('确认', f'删除班组 "{gname}"？\n该班组下有 {count} 名工人，将被一并删除！', parent=self.top):
            WorkerService.delete_group(gname)
            self.refresh()
