"""工人管理对话框"""
from tkinter import messagebox
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

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除工人 "{vals[0]}"？'):
            WorkerService.delete(int(item))
            self.refresh()
