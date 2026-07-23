"""
物料管理对话框 — 管理物料编号、名称、版本
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, END, messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from models.material import MaterialRepository
from ui.widgets.crud_dialog_base import CrudDialogBase


class MaterialDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title='管理物料',
            geometry='650x450',
            columns=[('code', '编号', 150), ('name', '名称', 180), ('version', '版本', 150)],
            add_fields=[('编号', 12), ('名称', 14), ('版本', 12)]
        )
        self._add_edit_btn()
        self._setup_code_combobox()

    def _setup_code_combobox(self):
        """把编号输入框改为可搜索下拉"""
        from tkinter import ttk
        # 获取编号输入框所在的 Frame
        code_entry = self._entries.get('编号')
        if not code_entry:
            return
        parent = code_entry.master
        # 获取所有物料编号作为下拉选项
        all_materials = MaterialRepository.get_all()
        code_list = sorted(set(m['code'] for m in all_materials))
        # 在相同位置创建 Combobox
        idx = code_entry.pack_info().get('side', 'left')
        code_entry.destroy()
        self._code_combobox = ttk.Combobox(parent, values=code_list, width=10,
                                            font=('Microsoft YaHei', 11))
        self._code_combobox.pack(side=idx, padx=(0, 4))
        # placeholder 效果
        self._code_combobox._ph_text = '编号'
        self._code_combobox.set('编号')
        self._code_combobox.config(foreground='#999999')
        def _code_in(e):
            if self._code_combobox.get() == '编号':
                self._code_combobox.set('')
                self._code_combobox.config(foreground='#333333')
        def _code_out(e):
            if not self._code_combobox.get().strip():
                self._code_combobox.set('编号')
                self._code_combobox.config(foreground='#999999')
        self._code_combobox.bind('<FocusIn>', _code_in, '+')
        self._code_combobox.bind('<FocusOut>', _code_out, '+')
        self._code_combobox.bind('<KeyRelease>', self._on_code_search)

        # ── 把名称输入框也改为可搜索下拉 ──
        name_entry = self._entries.get('名称')
        if not name_entry:
            return
        nparent = name_entry.master
        name_list = sorted(set(m['name'] for m in all_materials))
        nidx = name_entry.pack_info().get('side', 'left')
        name_entry.destroy()
        self._name_combobox = ttk.Combobox(nparent, values=name_list, width=12,
                                            font=('Microsoft YaHei', 11))
        self._name_combobox.pack(side=nidx, padx=(0, 4))
        self._name_combobox._ph_text = '名称'
        self._name_combobox.set('名称')
        self._name_combobox.config(foreground='#999999')
        def _name_in(e):
            if self._name_combobox.get() == '名称':
                self._name_combobox.set('')
                self._name_combobox.config(foreground='#333333')
        def _name_out(e):
            if not self._name_combobox.get().strip():
                self._name_combobox.set('名称')
                self._name_combobox.config(foreground='#999999')
        self._name_combobox.bind('<FocusIn>', _name_in, '+')
        self._name_combobox.bind('<FocusOut>', _name_out, '+')
        self._name_combobox.bind('<KeyRelease>', self._on_name_search)
        self._entries['名称'] = self._name_combobox
        self._entries['编号'] = self._code_combobox

    def _on_code_search(self, ev):
        """编号下拉输入关键字过滤"""
        kw = self._code_combobox.get()
        cur = kw
        all_materials = MaterialRepository.get_all()
        code_list = sorted(set(m['code'] for m in all_materials))
        if kw.strip() and kw != '编号':
            filtered = [c for c in code_list if kw.lower() in c.lower()]
            self._code_combobox['values'] = filtered
        else:
            self._code_combobox['values'] = code_list
        if cur != self._code_combobox.get():
            self._code_combobox.set(cur)

    def _on_name_search(self, ev):
        """名称下拉输入关键字过滤"""
        kw = self._name_combobox.get()
        cur = kw
        all_materials = MaterialRepository.get_all()
        name_list = sorted(set(m['name'] for m in all_materials))
        if kw.strip() and kw != '名称':
            filtered = [n for n in name_list if kw.lower() in n.lower()]
            self._name_combobox['values'] = filtered
        else:
            self._name_combobox['values'] = name_list
        if cur != self._name_combobox.get():
            self._name_combobox.set(cur)

    def clear_entries(self):
        """清空输入框（重写：Combobox 用 set 清空）"""
        for label, e in self._entries.items():
            if hasattr(e, 'set'):  # Combobox
                e.set('')
            else:
                e.delete(0, END)

    def _add_edit_btn(self):
        for child in self.top.winfo_children():
            if isinstance(child, Frame) and child != self.tree.master:
                for c in child.winfo_children():
                    if isinstance(c, Frame):
                        Button(c, text='编辑', bg=PRIMARY, fg='white',
                               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
                               padx=8, cursor='hand2',
                               command=self.on_edit).pack(side='left', padx=(4, 0))
                        return

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in MaterialRepository.get_all():
            self.tree.insert('', 'end', iid=str(r['id']),
                           values=(r['code'], r['name'], r['version']))

    def on_add(self):
        code = self.get_entry_value('编号')
        name = self.get_entry_value('名称')
        version = self.get_entry_value('版本')
        if not code or not name:
            messagebox.showinfo('提示', '请输入物料编号和名称', parent=self.top)
            return
        if MaterialRepository.add(code, name, version):
            self.refresh()
            self.clear_entries()
        else:
            messagebox.showinfo('提示', '物料编号已存在', parent=self.top)

    def on_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个物料', parent=self.top)
            return
        item = sel[0]
        mid = int(item)

        # 从数据库获取当前信息
        from models.database import Database
        conn = Database.get_conn()
        row = conn.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            messagebox.showerror('错误', '无法获取物料信息', parent=self.top)
            return

        top = Toplevel(self.top)
        top.title('编辑物料')
        top.geometry('350x200')
        top.configure(bg=CARD)
        top.transient(self.top)
        top.grab_set()
        top.focus_force()
        top.lift()

        Label(top, text='修改物料信息', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        Label(f, text='编号:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky='w', pady=3)
        from tkinter import ttk
        e_code = ttk.Combobox(f, values=sorted(set(m['code'] for m in MaterialRepository.get_all())),
                              width=16, font=('Microsoft YaHei', 10))
        e_code.set(row['code'])
        e_code.grid(row=0, column=1, pady=3, padx=(4, 0))
        Label(f, text='名称:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky='w', pady=3)
        e_name = ttk.Combobox(f, values=sorted(set(m['name'] for m in MaterialRepository.get_all())),
                              width=18, font=('Microsoft YaHei', 10))
        e_name.set(row['name'])
        e_name.grid(row=1, column=1, pady=3, padx=(4, 0))
        Label(f, text='版本:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=2, column=0, sticky='w', pady=3)
        e_ver = Entry(f, width=18, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_ver.insert(0, row['version'])
        e_ver.grid(row=2, column=1, pady=3, padx=(4, 0))

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack(pady=(4, 0))

        def do_save():
            nc = e_code.get().strip()
            nn = e_name.get().strip()
            nv = e_ver.get().strip()
            if not nc or not nn:
                err.config(text='编号和名称不能为空')
                return
            MaterialRepository.update(mid, nc, nn, nv)
            top.destroy()
            self._save_and_refresh()
            messagebox.showinfo('成功', '物料已更新', parent=self.top)

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除物料 "{vals[0]}({vals[1]}-{vals[2]})"？\n关联的工序和记录也将被删除！', parent=self.top):
            MaterialRepository.delete(int(item))
            self._save_and_refresh()
