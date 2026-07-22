"""
物料管理对话框 — 管理物料名称，显示工序总价
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, END, W, messagebox
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
        vals = self.tree.item(item, 'values')
        logger.debug(f'物料编辑: iid={item}, values={vals}')

        # 防御性处理：确保 values 不为空
        if not vals or not vals[0]:
            logger.warning(f'物料编辑: 选中行的值为空, iid={item}')
            # 尝试从数据库重新获取
            mid = int(item)
            conn = Database.get_conn()
            row = conn.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
            if row:
                old_name = row['name']
                logger.info(f'物料编辑: 从数据库重新获取名称={old_name}')
            else:
                messagebox.showerror('错误', '无法获取物料信息')
                return
        else:
            old_name = vals[0]

        mid = int(item)  # iid = material id

        # 弹出编辑对话框
        top = Toplevel(self.top)
        top.title('编辑物料')
        top.geometry('320x150')
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(self.top)

        Label(top, text='修改物料名称', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 6))

        f = Frame(top, bg=CARD)
        f.pack(padx=20)
        Label(f, text='名称:', bg=CARD, font=('Microsoft YaHei', 9)).pack(side=LEFT)
        e_name = Entry(f, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        e_name.insert(0, old_name if old_name else '')
        e_name.pack(side=LEFT, padx=(4, 0))
        e_name.focus()
        e_name.select_range(0, END)

        err = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err.pack(pady=(4, 0))

        def do_save():
            new_name = e_name.get().strip()
            if not new_name:
                err.config(text='名称不能为空')
                return
            MaterialRepository.update(mid, new_name, 0)
            top.destroy()
            self.refresh()
            messagebox.showinfo('成功', '物料已更新')

        Button(top, text='保存', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=2, cursor='hand2',
               command=do_save).pack(pady=(8, 4))

    def _on_delete_selected(self, item):
        vals = self.tree.item(item, 'values')
        if messagebox.askyesno('确认', f'删除物料 "{vals[0]}"？'):
            MaterialRepository.delete(int(item))  # iid = material id
            self.refresh()
