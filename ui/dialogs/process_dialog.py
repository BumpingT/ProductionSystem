"""
工序管理对话框
"""
from tkinter import messagebox
from models.process import ProcessRepository
from ui.widgets.crud_dialog_base import CrudDialogBase


class ProcessDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title='管理工序',
            geometry='600x450',
            columns=[('material', '物料', 130), ('process', '工序', 200), ('price', '单价', 80)],
            add_fields=[('物料', 10), ('工序', 12), ('单价', 6)]
        )

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in ProcessRepository.get_all():
            self.tree.insert('', 'end', iid=str(p['id']),
                           values=(p['material'], p['process_name'], p['unit_price']))

    def on_add(self):
        material = self.get_entry_value('物料')
        process = self.get_entry_value('工序')
        price_str = self.get_entry_value('单价')
        if not material or not process:
            messagebox.showinfo('提示', '请输入物料和工序名称')
            return
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            messagebox.showinfo('提示', '单价必须为数字')
            return
        if ProcessRepository.add(material, process, price):
            self.refresh()
            self.clear_entries()
        else:
            messagebox.showinfo('提示', '工序已存在')

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除工序 "{vals[1]}"？'):
            ProcessRepository.delete(int(item))
            self.refresh()
