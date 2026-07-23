"""
工序管理对话框 — 物料可搜索下拉，工序可搜索下拉，无工人分配
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from models.material import MaterialRepository
from services.process_service import ProcessService


class ProcessDialog:
    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title('管理工序')
        self.top.geometry('800x450')
        self.top.configure(bg=CARD)
        self.top.grab_set()

        Label(self.top, text='工序列表', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))

        # ── 工序列表 ──
        self.tree = ttk.Treeview(self.top, columns=('material', 'process', 'price'),
                                  show='headings', height=10)
        self.tree.heading('material', text='物料')
        self.tree.heading('process', text='工序')
        self.tree.heading('price', text='单价')
        self.tree.column('material', width=200, anchor='center')
        self.tree.column('process', width=200, anchor='center')
        self.tree.column('price', width=80, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=16)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # ── 添加/编辑区域 ──
        f = Frame(self.top, bg=CARD)
        f.pack(fill='x', padx=16, pady=6)

        Label(f, text='物料:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')

        # 物料可搜索下拉（显示 编号(名称)-版本）
        self.material_list = []  # 保存物料列表 [(code, display_text), ...]
        self._load_materials()
        self.cb_material = ttk.Combobox(f, values=[m[1] for m in self.material_list],
                                         width=24, font=('Microsoft YaHei', 10))
        self.cb_material.pack(side='left', padx=(2, 8))
        self.cb_material.bind('<KeyRelease>', self._on_material_keyup)

        Label(f, text='工序:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        self.process_names = []  # 保存所有工序名
        self.cb_process = ttk.Combobox(f, width=14, font=('Microsoft YaHei', 10))
        self.cb_process.pack(side='left', padx=(2, 8))
        self.cb_process.bind('<KeyRelease>', self._on_process_keyup)

        Label(f, text='单价:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side='left')
        self.e_price = Entry(f, width=8, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_price.pack(side='left', padx=(2, 8))

        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self._on_add).pack(side='left')
        Button(f, text='编辑', bg=PRIMARY, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self._on_edit).pack(side='left', padx=(4, 0))
        Button(f, text='删除选中', bg=RED, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=12, cursor='hand2', command=self._on_delete).pack(side='left', padx=(4, 0))

        self.refresh()

    def _load_materials(self):
        """加载物料列表（编号+名称+版本）"""
        materials = MaterialRepository.get_all()
        self.material_list = []
        for m in materials:
            ver = f"-{m['version']}" if m['version'] else ''
            display = f"{m['code']}({m['name']}){ver}"
            self.material_list.append((m['code'], display))

    def _load_process_names(self):
        """加载所有工序名"""
        self.process_names = ProcessService.get_process_names()
        self.cb_process['values'] = self.process_names

    def _on_material_keyup(self, ev):
        """物料下拉输入关键字过滤"""
        kw = self.cb_material.get()
        cur = kw  # 保存当前输入
        if not kw.strip():
            self.cb_material['values'] = [m[1] for m in self.material_list]
        else:
            filtered = [m[1] for m in self.material_list if kw.lower() in m[1].lower()]
            self.cb_material['values'] = filtered
        # 恢复输入内容（更新 values 后可能被清空）
        if cur != self.cb_material.get():
            self.cb_material.set(cur)

    def _on_process_keyup(self, ev):
        """工序下拉输入关键字过滤"""
        kw = self.cb_process.get()
        cur = kw  # 保存当前输入
        if not kw.strip():
            self.cb_process['values'] = self.process_names
        else:
            filtered = [n for n in self.process_names if kw.lower() in n.lower()]
            self.cb_process['values'] = filtered
        if cur != self.cb_process.get():
            self.cb_process.set(cur)

    def _get_selected_material_code(self) -> str:
        """从下拉选中值提取物料编号"""
        sel = self.cb_material.get().strip()
        for code, display in self.material_list:
            if display == sel:
                return code
        # 如果输入的是编号本身
        for code, display in self.material_list:
            if code == sel:
                return code
        return sel  # 原样返回

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in ProcessService.get_all():
            # 组装显示文本：编号(名称)-版本
            ver = f"-{p.get('material_version', '')}" if p.get('material_version') else ''
            mat_display = f"{p['material_code']}({p.get('material_name', '')}){ver}"
            self.tree.insert('', 'end', iid=str(p['id']),
                           values=(mat_display, p['process_name'], p['unit_price']))
        self._load_materials()
        self._load_process_names()

    def _save_and_refresh(self):
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

    def _on_select(self, ev):
        """选中工序行，自动填充表单"""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        # 物料下拉设置值
        self.cb_material.set(vals[0])
        self.cb_process.set(vals[1])
        self.e_price.delete(0, END)
        self.e_price.insert(0, vals[2])

    def _on_add(self):
        mat_display = self.cb_material.get().strip()
        process = self.cb_process.get().strip()
        price_str = self.e_price.get().strip()
        if not mat_display:
            messagebox.showinfo('提示', '请选择物料', parent=self.top)
            return
        if not process:
            messagebox.showinfo('提示', '请输入工序名称', parent=self.top)
            return
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            messagebox.showinfo('提示', '单价必须为数字', parent=self.top)
            return
        material_code = self._get_selected_material_code()
        if ProcessService.add(material_code, process, price):
            self.cb_material.set('')
            self.cb_process.set('')
            self.e_price.delete(0, END)
            self.refresh()
        else:
            messagebox.showinfo('提示', '该物料下工序已存在', parent=self.top)

    def _on_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个工序', parent=self.top)
            return
        item = sel[0]
        vals = self.tree.item(item, 'values')
        pid = int(item)

        # 获取当前工序信息
        from models.process import ProcessRepository
        all_p = ProcessRepository.get_all()
        proc = next((p for p in all_p if p['id'] == pid), None)
        if not proc:
            return

        top = Toplevel(self.top)
        top.title('编辑工序')
        top.geometry('380x200')
        top.configure(bg=CARD)
        top.transient(self.top)
        top.grab_set()
        top.focus_force()
        top.lift()

        Label(top, text='修改工序信息', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)

        Label(f, text='物料:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky='w', pady=3)
        mat_list = [m[1] for m in self.material_list]
        cb_mat = ttk.Combobox(f, values=mat_list, width=22, font=('Microsoft YaHei', 10))
        # 设置当前值
        ver = f"-{proc.get('material_version', '')}" if proc.get('material_version') else ''
        cur_display = f"{proc['material_code']}({proc.get('material_name', '')}){ver}"
        cb_mat.set(cur_display)
        cb_mat.grid(row=0, column=1, pady=3, padx=(4, 0))

        Label(f, text='工序:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky='w', pady=3)
        e_proc = ttk.Combobox(f, values=self.process_names, width=20, font=('Microsoft YaHei', 10))
        e_proc.set(proc['process_name'])
        e_proc.grid(row=1, column=1, pady=3, padx=(4, 0))

        Label(f, text='单价:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky='w', pady=3)
        e_price = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_price.insert(0, str(proc['unit_price']))
        e_price.grid(row=2, column=1, pady=3, padx=(4, 0))

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack()

        def do_save():
            md = cb_mat.get().strip()
            np_ = e_proc.get().strip()
            ps = e_price.get().strip()
            if not md or not np_:
                err.config(text='物料和工序不能为空')
                return
            try:
                pr = float(ps) if ps else 0
            except ValueError:
                err.config(text='单价必须为数字')
                return
            # 从显示文本提取物料编号
            mc = md
            for code, display in self.material_list:
                if display == md:
                    mc = code
                    break
            ProcessService.update(pid, mc, np_, pr)
            top.destroy()
            self._save_and_refresh()
            messagebox.showinfo('成功', '工序已更新', parent=self.top)

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        if messagebox.askyesno('确认', f'删除工序 "{vals[1]}"（{vals[0]}）？\n关联的生产记录也将被删除！', parent=self.top):
            ProcessService.delete(int(sel[0]))
            self.refresh()
