"""
工序管理对话框 — 含工人分配功能
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, Checkbutton, IntVar
from tkinter import messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from models.worker import WorkerRepository
from services.process_service import ProcessService


class ProcessDialog:
    def __init__(self, parent):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title('管理工序')
        self.top.geometry('750x550')
        self.top.configure(bg=CARD)
        self.top.grab_set()

        Label(self.top, text='工序列表', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))

        # ── 工序列表 ──
        self.tree = ttk.Treeview(self.top, columns=('material', 'process', 'price'),
                                  show='headings', height=8)
        self.tree.heading('material', text='物料')
        self.tree.heading('process', text='工序')
        self.tree.heading('price', text='单价')
        self.tree.column('material', width=130)
        self.tree.column('process', width=200)
        self.tree.column('price', width=80)
        self.tree.pack(fill='x', padx=16)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # ── 添加/删除区域 ──
        f = Frame(self.top, bg=CARD)
        f.pack(fill='x', padx=16, pady=4)
        self.e_material = Entry(f, width=10, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_material.pack(side='left', padx=(0, 4))
        self._ph(self.e_material, '物料')
        self.e_process = Entry(f, width=12, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_process.pack(side='left', padx=(0, 4))
        self._ph(self.e_process, '工序')
        self.e_price = Entry(f, width=6, font=('Microsoft YaHei', 11), relief='solid', bd=1)
        self.e_price.pack(side='left', padx=(0, 4))
        self._ph(self.e_price, '单价')

        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self._on_add).pack(side='left')
        Button(f, text='编辑', bg=PRIMARY, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self._on_edit).pack(side='left', padx=(4, 0))
        Button(f, text='删除', bg=RED, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self._on_delete).pack(side='left', padx=(4, 0))

        # ── 工人分配区域 ──
        assign_frame = Frame(self.top, bg=CARD, highlightbackground='#ddd', highlightthickness=1)
        assign_frame.pack(fill='both', expand=True, padx=16, pady=(8, 8))

        Label(assign_frame, text='工人分配（选中工序后操作）', font=('Microsoft YaHei', 10, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=12, pady=(8, 2))

        self.assign_info = Label(assign_frame, text='请选中一个工序', bg=CARD, fg='#888',
                                 font=('Microsoft YaHei', 9))
        self.assign_info.pack(anchor=W, padx=12)

        # Scrollable worker list
        import tkinter as tk
        canvas = tk.Canvas(assign_frame, bg=CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(assign_frame, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        self.worker_frame = Frame(canvas, bg=CARD)
        canvas.create_window((0, 0), window=self.worker_frame, anchor='nw')
        self.worker_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        canvas.pack(side='left', fill='both', expand=True, padx=(12, 0), pady=(0, 8))
        vsb.pack(side='right', fill='y', pady=(0, 8))

        self.selected_process_id = None
        self._worker_vars = {}
        self.refresh()

    def _ph(self, entry, text):
        entry._ph_text = text
        entry.insert(0, text)
        entry.config(fg='#999999')
        def _in(e):
            if entry.get() == entry._ph_text:
                entry.delete(0, END)
                entry.config(fg='#333333')
        def _out(e):
            if not entry.get().strip():
                entry.insert(0, entry._ph_text)
                entry.config(fg='#999999')
        entry.bind('<FocusIn>', _in, '+')
        entry.bind('<FocusOut>', _out, '+')

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in ProcessService.get_all():
            self.tree.insert('', 'end', iid=str(p['id']),
                           values=(p['material'], p['process_name'], p['unit_price']))
        self._refresh_workers()

    def _refresh_workers(self):
        """刷新工人分配列表"""
        for w in self.worker_frame.winfo_children():
            w.destroy()
        self._worker_vars = {}

        if not self.selected_process_id:
            self.assign_info.config(text='请选中一个工序')
            return

        assigned_ids = ProcessService.get_worker_processes(self.selected_process_id)
        self.assign_info.config(
            text=f'已分配 {len(assigned_ids)} 个工人，勾选/取消勾选以分配')

        for w in WorkerRepository.get_all():
            var = IntVar(value=1 if w['id'] in assigned_ids else 0)
            self._worker_vars[w['id']] = var

            def make_cmd(wid, pid):
                return lambda: self._toggle_worker(wid, pid)

            cb = Checkbutton(self.worker_frame, text=f"{w['name']} ({w['group_name']})",
                           variable=var, bg=CARD, font=('Microsoft YaHei', 9),
                           command=make_cmd(w['id'], self.selected_process_id))
            cb.pack(anchor=W, padx=8, pady=1)

    def _toggle_worker(self, worker_id, process_id):
        """切换工人工序分配"""
        if self._worker_vars.get(worker_id, IntVar()).get():
            ProcessService.assign_worker(worker_id, process_id)
        else:
            ProcessService.unassign_worker(worker_id, process_id)

    def _on_select(self, ev):
        sel = self.tree.selection()
        if sel:
            self.selected_process_id = int(sel[0])
        else:
            self.selected_process_id = None
        self._refresh_workers()

    def _on_add(self):
        material = self.e_material.get().strip()
        process = self.e_process.get().strip()
        price_str = self.e_price.get().strip()
        if material == getattr(self.e_material, '_ph_text', None): material = ''
        if process == getattr(self.e_process, '_ph_text', None): process = ''
        if not material or not process:
            messagebox.showinfo('提示', '请输入物料和工序名称')
            return
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            messagebox.showinfo('提示', '单价必须为数字')
            return
        if ProcessService.add(material, process, price):
            self.e_material.delete(0, END)
            self.e_process.delete(0, END)
            self.e_price.delete(0, END)
            self.refresh()
        else:
            messagebox.showinfo('提示', '工序已存在')

    def _on_edit(self):
        """编辑选中的工序"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个工序')
            return
        item = sel[0]
        vals = self.tree.item(item, 'values')
        pid = int(item)

        top = Toplevel(self.top)
        top.title('编辑工序')
        top.geometry('320x180')
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(self.top)

        Label(top, text='修改工序信息', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        Label(f, text='物料:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=W, pady=3)
        e_mat = Entry(f, width=16, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_mat.insert(0, vals[0])
        e_mat.grid(row=0, column=1, pady=3, padx=(4, 0))
        Label(f, text='工序:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=W, pady=3)
        e_proc = Entry(f, width=16, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_proc.insert(0, vals[1])
        e_proc.grid(row=1, column=1, pady=3, padx=(4, 0))
        Label(f, text='单价:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky=W, pady=3)
        e_price = Entry(f, width=16, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_price.insert(0, vals[2])
        e_price.grid(row=2, column=1, pady=3, padx=(4, 0))

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack()

        def do_save():
            nm = e_mat.get().strip()
            np_ = e_proc.get().strip()
            ps = e_price.get().strip()
            if not nm or not np_:
                err.config(text='物料和工序不能为空')
                return
            try:
                pr = float(ps) if ps else 0
            except ValueError:
                err.config(text='单价必须为数字')
                return
            ProcessService.update(pid, nm, np_, pr)
            top.destroy()
            self.refresh()
            messagebox.showinfo('成功', '工序已更新')

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        if messagebox.askyesno('确认', f'删除工序 "{vals[1]}"？'):
            ProcessService.delete(int(sel[0]))
            self.selected_process_id = None
            self.refresh()
