"""工人管理对话框"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, messagebox
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from services.worker_service import WorkerService
from ui.widgets.crud_dialog_base import CrudDialogBase


class WorkerDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title='管理工人',
            geometry='620x500',
            columns=[('name', '姓名', 180), ('group', '组别', 200)],
            add_fields=[('姓名', 12), ('组别', 12)]
        )
        self._add_edit_btn()

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
        for w in WorkerService.get_all():
            self.tree.insert('', 'end', iid=str(w['id']), values=(w['name'], w['group_name']))

    def on_add(self):
        name = self.get_entry_value('姓名')
        group = self.get_entry_value('组别')
        if not name:
            messagebox.showinfo('提示', '请输入工人姓名')
            return
        if WorkerService.add(name, group):
            self.refresh()
            self.clear_entries()
        else:
            messagebox.showinfo('提示', '工人已存在')

    def on_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个工人')
            return
        item = sel[0]
        vals = self.tree.item(item, 'values')
        wid = int(item)

        top = Toplevel(self.top)
        top.title('编辑工人')
        top.geometry('300x160')
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(self.top)

        Label(top, text='修改工人信息', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        Label(f, text='姓名:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=0, column=0, sticky=W, pady=3)
        e_name = Entry(f, width=18, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_name.insert(0, vals[0])
        e_name.grid(row=0, column=1, pady=3, padx=(4, 0))
        Label(f, text='组别:', bg=CARD, font=('Microsoft YaHei', 9)).grid(row=1, column=0, sticky=W, pady=3)
        e_group = Entry(f, width=18, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_group.insert(0, vals[1])
        e_group.grid(row=1, column=1, pady=3, padx=(4, 0))

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack()

        def do_save():
            nn = e_name.get().strip()
            ng = e_group.get().strip()
            if not nn:
                err.config(text='姓名不能为空')
                return
            WorkerService.update(wid, nn, ng)
            top.destroy()
            self.refresh()
            messagebox.showinfo('成功', '工人信息已更新')

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除工人 "{vals[0]}"？'):
            WorkerService.delete(int(item))
            self.refresh()
