"""
编辑记录对话框 — 从 DashboardView 拆分为独立组件
"""
from tkinter import Toplevel, Label, Frame, Button, Entry, ttk, W, CENTER, LEFT, X, END, RIGHT, Y, BOTH
from tkinter import messagebox
from config import CARD, DARK, ACCENT, RED, YEN
from models.record import RecordRepository
from models.worker import WorkerRepository
from models.process import ProcessRepository
from utils.logger import logger


def _format_process_display(p: dict) -> str:
    """格式化工序显示文本：编号(名称)-版本 / 工序名"""
    ver = f"-{p.get('material_version', '')}" if p.get('material_version') else ''
    return f"{p['material_code']}({p.get('material_name', '')}){ver} / {p['process_name']}"


class EditRecordDialog:
    """编辑单条生产记录"""

    def __init__(self, parent_root, record_id, current_user, on_save_callback=None):
        """
        parent_root: 主窗口 root（用于计算居中位置）
        record_id: 要编辑的记录 ID
        current_user: 当前用户 dict
        on_save_callback: 保存成功后的回调
        """
        self.root = parent_root
        self.record_id = record_id
        self.current_user = current_user
        self.on_save_callback = on_save_callback

        # 获取记录完整数据
        records = RecordRepository.get_all(self.current_user)
        self.record = None
        for r in records:
            if r['id'] == record_id:
                self.record = r
                break

        if not self.record:
            messagebox.showerror('错误', '未找到该记录')
            return

        # 权限验证
        self._check_permission()
        self._build()

    def _check_permission(self):
        """权限验证：普通工人只能编辑自己的记录"""
        user = self.current_user
        if not user:
            return
        role = user.get('role', '')
        if role == 'worker':
            wid = user.get('worker_id')
            if not wid:
                messagebox.showinfo('提示', '您未关联工人，不能编辑记录')
                raise PermissionError('无权限')
            if self.record['worker_id'] != wid:
                messagebox.showinfo('提示', '您只能编辑自己的记录')
                raise PermissionError('无权限')

    def _build(self):
        self.top = Toplevel(self.root)
        self.top.title('编辑记录')
        self.top.geometry('520x350')
        self.top.configure(bg=CARD)
        self.top.resizable(False, False)
        self.top.grab_set()
        self.top.transient(self.root)
        xp = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        yp = self.root.winfo_y() + self.root.winfo_height() // 2 - 175
        self.top.geometry(f'+{xp}+{yp}')

        Label(self.top, text='编辑生产记录', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(12, 10))

        ff = Frame(self.top, bg=CARD)
        ff.pack(padx=24, fill=X)

        # 记录 ID（可编辑）
        row0 = Frame(ff, bg=CARD)
        row0.pack(fill=X, pady=2)
        Label(row0, text='记录 ID：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        self.e_id = Entry(row0, width=10, font=('Microsoft YaHei', 11),
                          relief='solid', bd=1, justify=CENTER)
        self.e_id.pack(side=LEFT)
        self.e_id.insert(0, str(self.record_id))
        Label(row0, text='（修改ID需确保不重复）', bg=CARD, fg='#888',
              font=('Microsoft YaHei', 8)).pack(side=LEFT, padx=(6, 0))

        # 工人下拉
        self.all_workers = WorkerRepository.get_all()
        self.all_processes = ProcessRepository.get_all()
        worker_names = [w['name'] for w in self.all_workers]
        orig_worker_id = self.record['worker_id']
        orig_process_id = self.record['process_id']

        row1 = Frame(ff, bg=CARD)
        row1.pack(fill=X, pady=2)
        Label(row1, text='工人：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        self.cb_worker = ttk.Combobox(row1, values=worker_names,
                                       width=20, font=('Microsoft YaHei', 10))
        self.cb_worker.pack(side=LEFT)

        # 工序下拉
        row2 = Frame(ff, bg=CARD)
        row2.pack(fill=X, pady=2)
        Label(row2, text='工序：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        self.cb_process = ttk.Combobox(row2, values=[],
                                        width=28, font=('Microsoft YaHei', 10))
        self.cb_process.pack(side=LEFT)

        self.price_label = Label(row2, text='', bg=CARD, fg=ACCENT,
                                 font=('Microsoft YaHei', 10, 'bold'))
        self.price_label.pack(side=LEFT, padx=(6, 0))

        # 件数输入
        row3 = Frame(ff, bg=CARD)
        row3.pack(fill=X, pady=2)
        Label(row3, text='件数：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        self.e_qty = Entry(row3, width=12, font=('Microsoft YaHei', 11),
                           relief='solid', bd=1, justify=CENTER)
        self.e_qty.pack(side=LEFT)

        # 日期输入
        row4 = Frame(ff, bg=CARD)
        row4.pack(fill=X, pady=2)
        Label(row4, text='日期：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        self.e_date = Entry(row4, width=14, font=('Microsoft YaHei', 11),
                            relief='solid', bd=1, justify=CENTER)
        self.e_date.pack(side=LEFT)
        self.e_date.bind('<Button-1>', lambda e: self._show_calendar(self.e_date))

        # 查找原始工人和工序的索引
        self.orig_worker_idx = 0
        for i, w in enumerate(self.all_workers):
            if w['id'] == orig_worker_id:
                self.orig_worker_idx = i
                break
        self.orig_process_id = orig_process_id

        # 绑定事件
        self.cb_worker.bind('<<ComboboxSelected>>', self._on_worker_sel)
        self.cb_process.bind('<<ComboboxSelected>>', self._on_process_sel)

        # 预填值
        self.cb_worker.current(self.orig_worker_idx)
        self._update_process_list(self.orig_worker_idx)
        self.e_qty.insert(0, str(self.record['quantity']))
        self.e_date.insert(0, self.record['record_date'])

        # 错误提示
        self.err_label = Label(self.top, text='', bg=CARD, fg=RED,
                               font=('Microsoft YaHei', 9))
        self.err_label.pack(pady=(4, 0))

        # 按钮区
        btn_frame = Frame(self.top, bg=CARD)
        btn_frame.pack(pady=(8, 0))
        Button(btn_frame, text='保存修改', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=3, cursor='hand2',
               command=self._do_save).pack(side=LEFT, padx=(0, 10))
        Button(btn_frame, text='取消', bg='#999', fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=3, cursor='hand2',
               command=self.top.destroy).pack(side=LEFT)

    def _update_process_list(self, w_idx):
        """根据选中的工人过滤工序列表"""
        if w_idx < 0 or w_idx >= len(self.all_workers):
            self.cb_process['values'] = []
            self.cb_process.set('')
            return
        wid = self.all_workers[w_idx]['id']
        filtered = self.all_processes
        proc_labels = [_format_process_display(p) for p in filtered]
        self.cb_process['values'] = proc_labels
        # 选中原始工序
        for i, p in enumerate(filtered):
            if p['id'] == self.orig_process_id:
                self.cb_process.current(i)
                self.price_label.config(text=f"单价: {YEN}{p['unit_price']}")
                break

    def _on_worker_sel(self, ev=None):
        idx = self.cb_worker.current()
        if idx >= 0:
            self._update_process_list(idx)

    def _on_process_sel(self, ev=None):
        idx = self.cb_process.current()
        if idx >= 0:
            wid_idx = self.cb_worker.current()
            if wid_idx >= 0 and wid_idx < len(self.all_workers):
                wid = self.all_workers[wid_idx]['id']
                filtered = self.all_processes
                if idx < len(filtered):
                    self.price_label.config(text=f"单价: {YEN}{filtered[idx]['unit_price']}")

    def _do_save(self):
        # 获取自定义ID
        id_s = self.e_id.get().strip()
        new_id = None
        if id_s:
            try:
                new_id = int(id_s)
                if new_id < 1:
                    self.err_label.config(text='ID必须为正整数')
                    return
            except ValueError:
                self.err_label.config(text='ID必须为正整数')
                return

        widx = self.cb_worker.current()
        pidx = self.cb_process.current()
        qty_s = self.e_qty.get().strip()
        d = self.e_date.get().strip()
        if widx < 0 or pidx < 0:
            self.err_label.config(text='请选择工人和工序')
            return
        if not qty_s:
            self.err_label.config(text='请填写件数')
            return
        try:
            qty_f = float(qty_s)
            if qty_f != int(qty_f):
                self.err_label.config(text='件数必须为正整数')
                return
            qty = int(qty_f)
        except ValueError:
            self.err_label.config(text='件数必须为正整数')
            return
        if qty < 1:
            self.err_label.config(text='件数必须大于0')
            return
        if not d:
            self.err_label.config(text='请填写日期')
            return

        wid = self.all_workers[widx]['id']
        filtered2 = self.all_processes
        if pidx >= len(filtered2):
            self.err_label.config(text='工序数据错误')
            return
        proc = filtered2[pidx]

        try:
            RecordRepository.update(self.record_id, wid, proc['id'], qty, proc['unit_price'], d, new_id=new_id)
        except ValueError as ve:
            self.err_label.config(text=str(ve))
            return

        messagebox.showinfo('成功', '记录已更新')
        self.top.destroy()
        if self.on_save_callback:
            self.on_save_callback()

    def _show_calendar(self, entry):
        """弹出日历选择器"""
        import calendar as cal_mod
        from tkinter import Toplevel, Button
        top = Toplevel(self.top)
        top.title('选择日期')
        top.geometry('300x260')
        top.resizable(False, False)
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(self.top)

        from datetime import date as dt_date
        now = dt_date.today()
        yy, mm = now.year, now.month

        def _refresh():
            for w in f.winfo_children():
                w.destroy()
            Label(f, text=f'{yy}年{mm:02d}月', bg=CARD, fg=DARK,
                  font=('Microsoft YaHei', 10, 'bold')).grid(row=0, column=0, columnspan=7, pady=4)
            for di, dn in enumerate(['一','二','三','四','五','六','日']):
                Label(f, text=dn, bg=CARD, fg='#888', font=('Microsoft YaHei', 8),
                      width=4).grid(row=1, column=di, pady=1)
            _, ld = cal_mod.monthrange(yy, mm)
            for d in range(1, ld + 1):
                wd = cal_mod.weekday(yy, mm, d)
                btn = Button(f, text=str(d), width=4, bg='white', relief='flat',
                           font=('Microsoft YaHei', 9), cursor='hand2',
                           command=lambda d=d: select(d))
                btn.grid(row=(d - 1) // 7 + 2, column=wd, padx=1, pady=1)

        def prev():
            nonlocal yy, mm
            mm -= 1
            if mm < 1: mm, yy = 12, yy - 1
            _refresh()

        def nxt():
            nonlocal yy, mm
            mm += 1
            if mm > 12: mm, yy = 1, yy + 1
            _refresh()

        def select(d):
            entry.delete(0, 'end')
            entry.insert(0, f'{yy}-{mm:02d}-{d:02d}')
            top.destroy()

        bf = Frame(top, bg=CARD)
        bf.pack(pady=(6, 0))
        Button(bf, text='‹ 上月', bg=CARD, relief='flat', cursor='hand2',
               font=('Microsoft YaHei', 9), command=prev).pack(side=LEFT, padx=10)
        Button(bf, text='下月 ›', bg=CARD, relief='flat', cursor='hand2',
               font=('Microsoft YaHei', 9), command=nxt).pack(side=LEFT, padx=10)
        f = Frame(top, bg=CARD)
        f.pack(pady=6)
        _refresh()
