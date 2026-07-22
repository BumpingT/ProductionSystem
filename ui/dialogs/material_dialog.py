"""
物料管理对话框
"""
from tkinter import messagebox
from models.material import MaterialRepository
from ui.widgets.crud_dialog_base import CrudDialogBase


class MaterialDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title='管理物料',
            geometry='500x400',
            columns=[('name', '名称', 200), ('price', '单价(元)', 100)],
            add_fields=[('名称', 12), ('单价', 8)]
        )

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for m in MaterialRepository.get_all():
            self.tree.insert('', 'end', iid=str(m['id']), values=(m['name'], m['price']))

    def on_add(self):
        name = self.get_entry_value('名称')
        price_str = self.get_entry_value('单价')
        if not name:
            messagebox.showinfo('提示', '请输入物料名称')
            return
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            messagebox.showinfo('提示', '单价必须为数字')
            return
        if MaterialRepository.add(name, price):
            self.refresh()
            self.clear_entries()
        else:
            messagebox.showinfo('提示', '物料已存在')

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除物料 "{vals[0]}"？'):
            MaterialRepository.delete(int(item))  # iid = material id
            self.refresh()
