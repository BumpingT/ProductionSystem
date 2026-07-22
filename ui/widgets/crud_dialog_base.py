"""
管理对话框基类 — 消除重复的 CRUD 对话框代码
"""
from tkinter import Toplevel, Label, Frame, Button, ttk, END, Entry, W
from config import CARD, DARK, ACCENT, RED, GREEN


class CrudDialogBase:
    """CRUD 管理对话框基类"""

    def __init__(self, parent, title, geometry, columns, add_fields=None):
        """
        parent: 父窗口
        title: 对话框标题
        geometry: 窗口大小 e.g. '500x400'
        columns: [(field_key, display_name, width), ...]
        add_fields: [(label, entry_width), ...] 添加区域的输入框定义
        """
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.title(title)
        self.top.geometry(geometry)
        self.top.configure(bg=CARD)
        self.top.grab_set()

        Label(self.top, text=title, font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))

        self.columns = columns
        self._build_tree()
        self._build_form(add_fields or [])
        self.refresh()

    def _build_tree(self):
        """构建列表树"""
        cols = [c[0] for c in self.columns]
        widths = {c[0]: c[2] for c in self.columns}
        headers = {c[0]: c[1] for c in self.columns}
        self.tree = ttk.Treeview(self.top, columns=cols, show='headings', height=10)
        for col in cols:
            self.tree.heading(col, text=headers.get(col, col))
            self.tree.column(col, width=widths.get(col, 100))
        self.tree.pack(fill='both', expand=True, padx=16)

    def _build_form(self, add_fields):
        """构建底部的添加/删除区域"""
        f = Frame(self.top, bg=CARD)
        f.pack(fill='x', padx=16, pady=6)

        self._entries = {}
        for label, width in add_fields:
            e = Entry(f, width=width, font=('Microsoft YaHei', 11), relief='solid', bd=1)
            e.pack(side='left', padx=(0, 4))
            self._entries[label] = e
            self._add_placeholder(e, label)

        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self.on_add).pack(side='left')
        Button(f, text='删除', bg=RED, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=8, cursor='hand2', command=self.on_delete).pack(side='left', padx=(4, 0))

    def _add_placeholder(self, entry, text):
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

    def get_entry_value(self, label):
        """获取输入框的值（去掉占位符）"""
        val = self._entries[label].get().strip()
        if val == getattr(self._entries[label], '_ph_text', None):
            return ''
        return val

    def clear_entries(self):
        """清空所有输入框"""
        for e in self._entries.values():
            e.delete(0, END)

    def refresh(self):
        """刷新列表，由子类覆盖"""
        pass

    def on_add(self):
        """添加按钮回调，由子类覆盖"""
        pass

    def on_delete(self):
        """删除按钮回调，由子类覆盖"""
        sel = self.tree.selection()
        if not sel:
            return
        self._on_delete_selected(sel[0])

    def _on_delete_selected(self, item):
        """删除选中项，由子类覆盖"""
        pass
