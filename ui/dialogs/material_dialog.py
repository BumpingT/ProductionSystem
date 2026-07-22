"""
物料管理对话框 — 管理物料名称，显示工序总价
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, messagebox, StringVar
from config import CARD, DARK, ACCENT, RED, GREEN, PRIMARY
from models.material import MaterialRepository
from models.database import Database
from ui.widgets.crud_dialog_base import CrudDialogBase
from utils.logger import logger


class MaterialDialog(CrudDialogBase):
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            title='管理物料',
            geometry='500x400',
            columns=[('name', '名称', 200), ('total_price', '工序总价(元)', 100)],
            add_fields=[('名称', 12)]
        )
        # 在按钮栏添加编辑按钮
        self._add_edit_btn()

    def _add_edit_btn(self):
        """在按钮栏添加编辑按钮"""
        # 找到按钮栏（最后一个 Frame）
        for child in self.top.winfo_children():
            if isinstance(child, Frame) and child != self.tree.master:
                for c in child.winfo_children():
                    if isinstance(c, Frame):
                        btn_frame = c
                        Button(btn_frame, text='编辑', bg=PRIMARY, fg='white',
                               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
                               padx=8, cursor='hand2',
                               command=self.on_edit).pack(side='left', padx=(4, 0))
                        return

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        conn = Database.get_conn()
        rows = conn.execute("""
            SELECT m.id, m.name,
                   COALESCE(ROUND(SUM(p.unit_price), 2), 0) AS total_price
            FROM materials m
            LEFT JOIN processes p ON m.name = p.material
            GROUP BY m.id
            ORDER BY m.name
        """).fetchall()
        for r in rows:
            self.tree.insert('', 'end', iid=str(r['id']),
                           values=(r['name'], r['total_price']))

    def on_add(self):
        name = self.get_entry_value('名称')
        if not name:
            messagebox.showinfo('提示', '请输入物料名称')
            return
        if MaterialRepository.add(name, 0):
            self.refresh()
            self.clear_entries()
        else:
            messagebox.showinfo('提示', '物料已存在')

    def on_edit(self):
        """编辑选中的物料名称"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选择一个物料')
            return
        item = sel[0]
        mid = int(item)

        # 从数据库获取当前名称
        conn = Database.get_conn()
        row = conn.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            messagebox.showerror('错误', '无法获取物料信息')
            return
        old_name = row['name']
        old_price = row['price']

        from tkinter.simpledialog import askstring
        new_name = askstring('编辑物料', '物料名称:', initialvalue=old_name,
                            parent=self.top)
        if new_name is not None:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showinfo('提示', '名称不能为空')
                return
            MaterialRepository.update(mid, new_name, old_price)
            self.refresh()
            messagebox.showinfo('成功', '物料已更新')

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除物料 "{vals[0]}"？'):
            MaterialRepository.delete(int(item))  # iid = material id
            self.refresh()
