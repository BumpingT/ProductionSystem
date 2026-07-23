"""
主面板视图 — 工具栏、记录表单、统计栏、数据表格、底部操作栏
"""
from tkinter import Frame, Label, Button, Entry, ttk, Scrollbar, VERTICAL, END, BOTH, X, Y, LEFT, RIGHT, W, CENTER
from tkinter import messagebox
from datetime import date
import os

from config import BG, CARD, PRIMARY, ACCENT, GREEN, RED, DARK, YEN, _BASE
from services.chart_service import gen_report
from services.export_service import export_excel
from services.process_service import ProcessService
from ui.dialogs.user_dialog import UserDialog
from models.record import RecordRepository
from models.database import Database
from models.worker import WorkerRepository
from models.process import ProcessRepository
from models.record import RecordRepository as StatsRepo
from models.user import UserRepository
from ui.dialogs.material_dialog import MaterialDialog
from ui.dialogs.worker_dialog import WorkerDialog
from ui.dialogs.process_dialog import ProcessDialog
from utils.auth import hash_password as _hash_pw, verify_password as _verify_pw
from utils.logger import logger


class DashboardView:
    def __init__(self, root, current_user, user_perms, on_logout=None):
        self.root = root
        self.current_user = current_user
        self.user_perms = user_perms
        self._on_logout = on_logout
        self._perm_widgets = []
        self._worker_ids = []
        self._worker_procs = {}
        self._tree = None
        self._stat_labels = {}
        self.cb_worker = None
        self._perm_vars = {}

        self._build()

    # ── Permission helpers ──
    def _check_perm(self, perm_key):
        if not self.current_user:
            return False
        if self.current_user.get('role') == 'admin':
            return True
        return bool(self.user_perms.get(perm_key, 0))

    def _apply_permissions(self):
        for widget_name, perm_key in self._perm_widgets:
            self._apply_to_child(self.root, widget_name, perm_key)

    def _apply_to_child(self, parent, widget_name, perm_key):
        if hasattr(parent, '_perm_name') and parent._perm_name == widget_name:
            try:
                parent.config(state='normal' if self._check_perm(perm_key) else 'disabled')
            except:
                pass
        for child in parent.winfo_children():
            self._apply_to_child(child, widget_name, perm_key)

    def _make_btn(self, tb, text, cmd, perm, bg_color):
        btn = Button(tb, text=text, command=cmd, bg=bg_color, fg='white',
                     font=('Microsoft YaHei', 9, 'bold'), relief='flat',
                     padx=10, pady=3, cursor='hand2')
        btn.pack(side=LEFT, padx=(0, 6))
        btn._perm_name = text
        self._perm_widgets.append((text, perm))
        return btn

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

    # ── Build main UI ──
    def _build(self):
        # Header
        hdr = Frame(self.root, bg=PRIMARY, height=64)
        hdr.pack(fill=X)
        hdr.pack_propagate(False)
        Label(hdr, text='生产记录管理系统', fg='white', bg=PRIMARY,
              font=('Microsoft YaHei', 16, 'bold')).pack(padx=24, pady=(10, 0), anchor=W)
        Label(hdr, text='工人 · 工序 · 产量 · 工价 · 动态图表', fg='#b0c4de',
              bg=PRIMARY, font=('Microsoft YaHei', 9)).pack(padx=24, pady=(0, 8), anchor=W)

        main = Frame(self.root, bg=BG)
        main.pack(fill=BOTH, expand=True, padx=12, pady=(10, 8))

        # ── Toolbar ──
        tb = Frame(main, bg=CARD)
        tb.pack(fill=X, pady=(0, 8))

        self._make_btn(tb, '管理物料', self._manage_materials, 'material_manage', PRIMARY)
        self._make_btn(tb, '管理工人', self._manage_workers, 'worker_manage', PRIMARY)
        self._make_btn(tb, '管理工序', self._manage_processes, 'process_manage', PRIMARY)
        self._make_btn(tb, '汇总查询', self._summary_page, 'summary_view', GREEN)
        if self._check_perm('user_manage'):
            self._make_btn(tb, '用户管理', self._manage_users, 'user_manage', RED)
            self._make_btn(tb, '权限管理', self._manage_permissions, 'user_manage', GREEN)

        # ── 筛选栏 ──
        filter_bar = Frame(main, bg=CARD, highlightbackground='#ddd',
                           highlightthickness=1, padx=10, pady=4)
        filter_bar.pack(fill=X, pady=(0, 6))
        Label(filter_bar, text='筛选：', bg=CARD, fg=DARK,
              font=('Microsoft YaHei', 9, 'bold')).pack(side=LEFT)
        Label(filter_bar, text='日期从', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(4, 0))
        self._filter_date_from = Entry(filter_bar, width=10, font=('Microsoft YaHei', 9),
                                        relief='solid', bd=1)
        self._filter_date_from.pack(side=LEFT, padx=(2, 2))
        self._filter_date_from.bind('<Button-1>', lambda e: self._show_calendar(self._filter_date_from))
        Label(filter_bar, text='至', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(2, 0))
        self._filter_date_to = Entry(filter_bar, width=10, font=('Microsoft YaHei', 9),
                                      relief='solid', bd=1)
        self._filter_date_to.pack(side=LEFT, padx=(2, 4))
        self._filter_date_to.bind('<Button-1>', lambda e: self._show_calendar(self._filter_date_to))
        Label(filter_bar, text='工人', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(4, 0))
        self._filter_worker = ttk.Combobox(filter_bar, values=[], state='readonly', width=10)
        self._filter_worker.pack(side=LEFT, padx=(2, 4))
        Label(filter_bar, text='工序', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(4, 0))
        self._filter_process = ttk.Combobox(filter_bar, values=[], state='readonly', width=14)
        self._filter_process.pack(side=LEFT, padx=(2, 4))
        Button(filter_bar, text='查询', bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2',
               command=self._apply_filter).pack(side=LEFT, padx=(4, 0))
        Button(filter_bar, text='重置', bg='#999', fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2',
               command=self._reset_filter).pack(side=LEFT, padx=(4, 0))

        # ── Record entry form ──
        fm = Frame(main, bg=CARD, highlightbackground='#ddd',
                   highlightthickness=1, padx=14, pady=10)
        fm.pack(fill=X, pady=(0, 10))
        Label(fm, text='添加记录', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W)
        row = Frame(fm, bg=CARD)
        row.pack(fill=X, pady=(6, 0))

        fw = Frame(row, bg=CARD)
        fw.pack(side=LEFT, padx=(0, 8))
        Label(fw, text='选择工人', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(anchor=W, padx=(2, 0))
        self.cb_worker = ttk.Combobox(fw, width=12, font=('Microsoft YaHei', 10),
                                      state='readonly')
        self.cb_worker.pack()

        fp = Frame(row, bg=CARD)
        fp.pack(side=LEFT, padx=(0, 8))
        Label(fp, text='选择工序', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(anchor=W, padx=(2, 0))
        self.cb_process = ttk.Combobox(fp, width=18, font=('Microsoft YaHei', 10),
                                       state='readonly')
        self.cb_process.pack()

        fq = Frame(row, bg=CARD)
        fq.pack(side=LEFT, padx=(0, 8))
        Label(fq, text='件数', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(anchor=W, padx=(2, 0))
        self.e_qty = Entry(fq, width=8, font=('Microsoft YaHei', 11),
                           relief='solid', bd=1, justify=CENTER)
        self.e_qty.pack()

        fd = Frame(row, bg=CARD)
        fd.pack(side=LEFT, padx=(0, 8))
        Label(fd, text='日期', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(anchor=W, padx=(2, 0))
        self.e_date = Entry(fd, width=12, font=('Microsoft YaHei', 11),
                            relief='solid', bd=1, justify=CENTER)
        self.e_date.pack()
        self.e_date.insert(0, date.today().isoformat())
        self.e_date.bind('<Button-1>', lambda e: self._show_calendar(self.e_date))

        self.price_label = Label(row, text='', bg=CARD, fg=ACCENT,
                                 font=('Microsoft YaHei', 10, 'bold'))
        self.price_label.pack(side=LEFT, padx=(4, 8))

        # Bind worker selection
        self.cb_worker.bind('<<ComboboxSelected>>', self._on_worker_sel)
        self.cb_process.bind('<<ComboboxSelected>>', self._on_process_sel)

        btn_frame = Frame(row, bg=CARD)
        btn_frame.pack(side=LEFT)
        Button(btn_frame, text='添加', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, pady=2, cursor='hand2',
               command=self._do_add).pack()

        del_frame = Frame(row, bg=CARD)
        del_frame.pack(side=LEFT, padx=(4, 0))
        btn_del = Button(del_frame, text='删除选中', bg=RED, fg='white',
                         font=('Microsoft YaHei', 9, 'bold'), relief='flat',
                         padx=10, pady=2, cursor='hand2',
                         command=self._delete_selected)
        btn_del.pack()
        btn_del._perm_name = '删除记录'
        self._perm_widgets.append(('删除记录', 'record_delete'))

        # ── Stats bar ──
        stats_bar = Frame(main, bg='white', relief='solid', bd=1)
        stats_bar.pack(fill=X, pady=(0, 6))
        for key, label in [('w', '工人数'), ('q', '总产量'), ('e', '总工价'), ('r', '记录数')]:
            cell = Frame(stats_bar, bg='white')
            cell.pack(side=LEFT, expand=True, padx=8, pady=6)
            Label(cell, text=label, bg='white', fg='#888',
                  font=('Microsoft YaHei', 8)).pack()
            self._stat_labels[key] = Label(cell, text='0', bg='white', fg=DARK,
                                           font=('Microsoft YaHei', 14, 'bold'))
            self._stat_labels[key].pack()

        # ── Records table ──
        tree_frame = Frame(main)
        tree_frame.pack(fill=BOTH, expand=True)
        self._tree = ttk.Treeview(tree_frame,
                                   columns=('id', 'material', 'process', 'worker',
                                            'group', 'qty', 'price', 'wage', 'date'),
                                   show='headings', height=12)
        col_defs = [('id', 'ID', 40), ('material', '物料', 80), ('process', '工序', 100),
                    ('worker', '姓名', 70), ('group', '组别', 70), ('qty', '件数', 60),
                    ('price', '单价', 60), ('wage', '工价', 70), ('date', '日期', 100)]
        for col, text, w in col_defs:
            self._tree.heading(col, text=text)
            self._tree.column(col, width=w, anchor=CENTER if col in ('id', 'qty', 'price', 'wage') else W)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb = Scrollbar(tree_frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)

        # 绑定双击编辑事件（使用 tree 级别绑定，确保始终有效）
        self._tree.bind('<Double-1>', self._edit_record)

        # ── Bottom buttons ──
        bottom = Frame(main, bg=BG)
        bottom.pack(fill=X, pady=(4, 0))
        Button(bottom, text='📊 生成图表报告', command=self._open_chart,
               bg=PRIMARY, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=10, cursor='hand2').pack(side=LEFT, padx=(0, 6))
        Button(bottom, text='📅 月度汇总', command=self._monthly_summary,
               bg=GREEN, fg='white', font=('Microsoft YaHei', 9, 'bold'),
               relief='flat', padx=10, cursor='hand2').pack(side=LEFT)

        # ── Status bar ──
        bt = Frame(self.root, bg='white', highlightbackground='#ddd',
                   highlightthickness=1)
        bt.pack(fill=X)
        if self.current_user:
            un = self.current_user.get('username', '')
            dn = self.current_user.get('display_name', '')
            role_en = self.current_user.get('role', '')
            from config import ROLE_NAMES
            role_cn = ROLE_NAMES.get(role_en, role_en)
            Label(bt, text=f'当前用户: {dn} ({un}) - {role_cn}', bg='white', fg='#888',
                  font=('Microsoft YaHei', 8)).pack(side=LEFT, padx=12)
        Button(bt, text='修改密码', bg='#2980b9', fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, pady=2, cursor='hand2',
               command=self._change_pw).pack(side=RIGHT, padx=(4, 4))
        Button(bt, text='退出登录', bg=DARK, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, pady=2, cursor='hand2',
               command=self._logout).pack(side=RIGHT, padx=(4, 4))

        # Initial data load
        self.refresh()
        self._apply_permissions()

    # ── Worker/Process selection linkage ──
    def _on_worker_sel(self, ev):
        sel = self.cb_worker.current()
        if sel < 0:
            return
        wid = self._worker_ids[sel] if sel < len(self._worker_ids) else 0
        if wid in self._worker_procs:
            procs = self._worker_procs[wid]
            self.cb_process['values'] = [f"{p['material']} - {p['process_name']}" for p in procs]
        else:
            self.cb_process['values'] = []
        self.cb_process.set('')

    def _on_process_sel(self, ev):
        sel = self.cb_process.current()
        if sel < 0:
            return
        wid = self.cb_worker.current()
        if wid >= 0 and wid < len(self._worker_ids):
            widsel = self._worker_ids[wid]
            procs = self._worker_procs.get(widsel, [])
            if sel < len(procs):
                self.price_label.config(text=f"单价: {YEN}{procs[sel]['unit_price']}")

    # ── CRUD operations ──
    def _do_add(self):
        wid = self.cb_worker.current()
        pid = self.cb_process.current()
        qty_s = self.e_qty.get().strip()
        d = self.e_date.get().strip()
        if wid < 0 or pid < 0 or not qty_s:
            messagebox.showinfo('提示', '请选择工人、工序并填写件数')
            return
        try:
            qty = float(qty_s)
        except ValueError:
            messagebox.showinfo('提示', '件数必须为数字')
            return
        if qty <= 0:
            messagebox.showinfo('提示', '件数必须大于0')
            return
        widsel = self._worker_ids[wid]
        proc_id = 0
        price = 0
        if widsel in self._worker_procs and pid < len(self._worker_procs[widsel]):
            proc = self._worker_procs[widsel][pid]
            proc_id = proc['id']
            price = proc['unit_price']
        if RecordRepository.add(widsel, proc_id, qty, price, d):
            self.e_qty.delete(0, END)
            self.refresh()
            messagebox.showinfo('成功', '记录已添加')
        else:
            messagebox.showerror('错误', '添加失败')

    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            return
        if not messagebox.askyesno('确认', '确定删除选中的记录？'):
            return
        for item in sel:
            vals = self._tree.item(item, 'values')
            if vals:
                RecordRepository.delete(int(vals[0]))
        self.refresh()

    def _edit_record(self, ev=None):
        """双击表格行编辑记录"""
        if not self._check_perm('record_edit'):
            messagebox.showinfo('提示', '您没有编辑记录的权限')
            return
        sel = self._tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self._tree.item(item, 'values')
        if not vals:
            return
        record_id = int(vals[0])

        # ── 业务限制：编辑权限 ──
        from datetime import date
        from models.record import RecordRepository as RR2
        user = self.current_user
        if user:
            role = user.get('role', '')
            # 普通工人只能编辑自己的记录
            if role == 'worker':
                wid = user.get('worker_id')
                if not wid:
                    messagebox.showinfo('提示', '您未关联工人，不能编辑记录')
                    return
                # 获取记录主人
                recs = RR2.get_all(user)
                rec = None
                for r in recs:
                    if r['id'] == record_id:
                        rec = r
                        break
                if rec and rec['worker_id'] != wid:
                    messagebox.showinfo('提示', '您只能编辑自己的记录')
                    return
            # 组长只能编辑本组记录
            if role == 'leader' and user.get('group_name'):
                recs = RR2.get_all(user)
                rec = None
                for r in recs:
                    if r['id'] == record_id:
                        rec = r
                        break
                if not rec:
                    messagebox.showinfo('提示', '您只能编辑本组工人的记录')
                    return

        # 从数据库重新获取完整记录
        records = RecordRepository.get_all(self.current_user)
        record = None
        for r in records:
            if r['id'] == record_id:
                record = r
                break
        if not record:
            messagebox.showerror('错误', '未找到该记录')
            return

        # 创建编辑对话框
        from tkinter import Toplevel
        top = Toplevel(self.root)
        top.title('编辑记录')
        top.geometry('520x350')
        top.configure(bg=CARD)
        top.resizable(False, False)
        top.grab_set()
        top.transient(self.root)
        xp = self.root.winfo_x() + self.root.winfo_width() // 2 - 260
        yp = self.root.winfo_y() + self.root.winfo_height() // 2 - 175
        top.geometry(f'+{xp}+{yp}')

        Label(top, text='编辑生产记录', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(12, 10))

        # 表单容器
        ff = Frame(top, bg=CARD)
        ff.pack(padx=24, fill=X)

        # 记录 ID（只读）
        row0 = Frame(ff, bg=CARD)
        row0.pack(fill=X, pady=2)
        Label(row0, text='记录 ID：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        e_id_lbl = Label(row0, text=str(record_id), bg=CARD, fg='#888',
                         font=('Microsoft YaHei', 10))
        e_id_lbl.pack(side=LEFT)

        # 工人下拉
        row1 = Frame(ff, bg=CARD)
        row1.pack(fill=X, pady=2)
        Label(row1, text='工人：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        all_workers = WorkerRepository.get_all()
        worker_names = [w['name'] for w in all_workers]
        cb_worker = ttk.Combobox(row1, values=worker_names, state='readonly',
                                 width=20, font=('Microsoft YaHei', 10))
        cb_worker.pack(side=LEFT)

        # 工序下拉
        row2 = Frame(ff, bg=CARD)
        row2.pack(fill=X, pady=2)
        Label(row2, text='工序：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        cb_process = ttk.Combobox(row2, values=[], state='readonly',
                                  width=28, font=('Microsoft YaHei', 10))
        cb_process.pack(side=LEFT)

        # 单价标签
        price_label = Label(row2, text='', bg=CARD, fg=ACCENT,
                            font=('Microsoft YaHei', 10, 'bold'))
        price_label.pack(side=LEFT, padx=(6, 0))

        # 件数输入
        row3 = Frame(ff, bg=CARD)
        row3.pack(fill=X, pady=2)
        Label(row3, text='件数：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        e_qty = Entry(row3, width=12, font=('Microsoft YaHei', 11),
                      relief='solid', bd=1, justify=CENTER)
        e_qty.pack(side=LEFT)

        # 日期输入
        row4 = Frame(ff, bg=CARD)
        row4.pack(fill=X, pady=2)
        Label(row4, text='日期：', bg=CARD, font=('Microsoft YaHei', 10),
              width=10, anchor=W).pack(side=LEFT)
        e_date = Entry(row4, width=14, font=('Microsoft YaHei', 11),
                       relief='solid', bd=1, justify=CENTER)
        e_date.pack(side=LEFT)
        e_date.bind('<Button-1>', lambda e: self._show_calendar(e_date))

        # 查找原始工人和工序的索引
        orig_worker_id = record['worker_id']
        orig_process_id = record['process_id']
        orig_worker_idx = 0
        for i, w in enumerate(all_workers):
            if w['id'] == orig_worker_id:
                orig_worker_idx = i
                break

        # 所有工序列表（用于过滤）
        all_processes = ProcessRepository.get_all()

        def _update_process_list(w_idx):
            """根据选中的工人过滤工序列表"""
            if w_idx < 0 or w_idx >= len(all_workers):
                cb_process['values'] = []
                cb_process.set('')
                return
            wid = all_workers[w_idx]['id']
            # 获取该工人可用的工序
            assigned_pids = set(ProcessService.get_worker_processes(wid))
            if assigned_pids:
                filtered = [p for p in all_processes if p['id'] in assigned_pids]
            else:
                filtered = all_processes  # 无分配则显示全部
            proc_labels = [f"{p['material']} - {p['process_name']}" for p in filtered]
            cb_process['values'] = proc_labels
            # 选中原始工序
            for i, p in enumerate(filtered):
                if p['id'] == orig_process_id:
                    cb_process.current(i)
                    price_label.config(text=f"单价: {YEN}{p['unit_price']}")
                    break
            return filtered

        def _on_worker_sel(ev=None):
            idx = cb_worker.current()
            if idx >= 0:
                _update_process_list(idx)

        def _on_process_sel(ev=None):
            idx = cb_process.current()
            if idx >= 0:
                vals2 = cb_process['values']
                wid_idx = cb_worker.current()
                if wid_idx >= 0 and wid_idx < len(all_workers):
                    wid = all_workers[wid_idx]['id']
                    assigned_pids = set(ProcessService.get_worker_processes(wid))
                    if assigned_pids:
                        filtered = [p for p in all_processes if p['id'] in assigned_pids]
                    else:
                        filtered = all_processes
                    if idx < len(filtered):
                        price_label.config(text=f"单价: {YEN}{filtered[idx]['unit_price']}")

        cb_worker.bind('<<ComboboxSelected>>', _on_worker_sel)
        cb_process.bind('<<ComboboxSelected>>', _on_process_sel)

        # 预填值
        cb_worker.current(orig_worker_idx)
        _update_process_list(orig_worker_idx)
        e_qty.insert(0, str(record['quantity']))
        e_date.insert(0, record['record_date'])

        # 错误提示
        err_label = Label(top, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err_label.pack(pady=(4, 0))

        def do_save():
            """保存编辑"""
            widx = cb_worker.current()
            pidx = cb_process.current()
            qty_s = e_qty.get().strip()
            d = e_date.get().strip()
            if widx < 0 or pidx < 0:
                err_label.config(text='请选择工人和工序')
                return
            if not qty_s:
                err_label.config(text='请填写件数')
                return
            try:
                qty = float(qty_s)
            except ValueError:
                err_label.config(text='件数必须为数字')
                return
            if not d:
                err_label.config(text='请填写日期')
                return

            # 获取选中的工序ID和单价
            wid = all_workers[widx]['id']
            assigned_pids2 = set(ProcessService.get_worker_processes(wid))
            if assigned_pids2:
                filtered2 = [p for p in all_processes if p['id'] in assigned_pids2]
            else:
                filtered2 = all_processes
            if pidx >= len(filtered2):
                err_label.config(text='工序数据错误')
                return
            proc = filtered2[pidx]

            # 更新数据库
            RecordRepository.update(record_id, wid, proc['id'], qty, proc['unit_price'], d)
            messagebox.showinfo('成功', '记录已更新')
            top.destroy()
            self.refresh()

        # 按钮区
        btn_frame = Frame(top, bg=CARD)
        btn_frame.pack(pady=(8, 0))
        Button(btn_frame, text='保存修改', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=3, cursor='hand2',
               command=do_save).pack(side=LEFT, padx=(0, 10))
        Button(btn_frame, text='取消', bg='#999', fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=16, pady=3, cursor='hand2',
               command=top.destroy).pack(side=LEFT)

    # ── Refresh ──
    def refresh(self):
        # 组长：使用 leader_workers 精确关联的工人
        from models.user import UserRepository as UR2
        is_leader = self.current_user and self.current_user.get('role') == 'leader'
        leader_wids = []
        if is_leader:
            leader_wids = UR2.get_leader_workers(self.current_user['username'])
        if leader_wids:
            all_workers = [w for w in WorkerRepository.get_all() if w['id'] in leader_wids]
        elif is_leader and self.current_user.get('group_name'):
            # 降级：按组别筛选
            lg = self.current_user.get('group_name', '')
            all_workers = [w for w in WorkerRepository.get_all() if w.get('group_name') == lg]
        else:
            all_workers = WorkerRepository.get_all()

        # Load workers and processes
        self._worker_ids = []
        self._worker_procs = {}
        for w in all_workers:
            self._worker_ids.append(w['id'])
            assigned_ids = ProcessService.get_worker_processes(w['id'])
            procs = [p for p in ProcessRepository.get_all() if p['id'] in assigned_ids]
            self._worker_procs[w['id']] = procs

        if hasattr(self, 'cb_worker') and self.cb_worker:
            self.cb_worker['values'] = [w['name'] for w in all_workers]
            # 普通工人只能选自己
            if self.current_user and self.current_user.get('role') == 'worker' and self.current_user.get('worker_id'):
                worker_name = ''
                for w in all_workers:
                    if w['id'] == self.current_user['worker_id']:
                        worker_name = w['name']
                        break
                if worker_name:
                    self.cb_worker.set(worker_name)
                    self.cb_worker.config(state='disabled')
                else:
                    self.cb_worker.config(state='readonly')
            else:
                self.cb_worker.config(state='readonly')

        # 填充筛选栏下拉框
        if hasattr(self, '_filter_worker'):
            self._filter_worker['values'] = ['(全部)'] + [w['name'] for w in all_workers]
            if not self._filter_worker.get():
                self._filter_worker.set('(全部)')
        if hasattr(self, '_filter_process'):
            all_procs = ProcessRepository.get_all()
            proc_names = sorted(set(p['material'] + ' - ' + p['process_name'] for p in all_procs))
            self._filter_process['values'] = ['(全部)'] + proc_names
            if not self._filter_process.get():
                self._filter_process.set('(全部)')

        # Refresh table
        self._refresh_table()

    def _refresh_table(self):
        if not self._tree:
            return
        self._tree.delete(*self._tree.get_children())
        records = RecordRepository.get_all(self.current_user)
        for r in records[:200]:
            wage = r['quantity'] * r['unit_price']
            item = self._tree.insert('', END, values=(
                r['id'], r['material'], r['process_name'], r['worker_name'],
                r['group_name'], r['quantity'], f'{YEN}{r["unit_price"]}',
                f'{YEN}{round(wage, 2)}', r['record_date']
            ))
            # 存储完整记录数据到 tags 中，供编辑时使用
            self._tree.item(item, tags=(str(r['id']),))

        # Update stats
        from models.record import RecordRepository as RR
        stats = RR.get_stats(user=self.current_user)
        t = stats.get('totals', {})
        self._stat_labels['w'].config(text=t.get('w', 0))
        self._stat_labels['q'].config(text=str(t.get('q', 0)))
        self._stat_labels['e'].config(text=f'{YEN}{round(t.get("e", 0), 2)}')
        self._stat_labels['r'].config(text=t.get('r', 0))

    def _apply_filter(self):
        """应用筛选条件"""
        try:
            sd = self._filter_date_from.get().strip()
            ed = self._filter_date_to.get().strip()
            wf = self._filter_worker.get() if hasattr(self, '_filter_worker') else '(全部)'
            pf = self._filter_process.get() if hasattr(self, '_filter_process') else '(全部)'

            # 查询记录
            if sd and ed and sd > ed:
                messagebox.showinfo('提示', '起始日期不能晚于结束日期')
                self._refresh_table()
                return
            self._tree.delete(*self._tree.get_children())
            conn = Database.get_conn()
            wh = []
            pa = []
            # 用户权限过滤（组长按组，工人按自己）
            if self.current_user:
                if self.current_user.get('role') == 'worker' and self.current_user.get('worker_id'):
                    wh.append("r.worker_id=?")
                    pa.append(self.current_user['worker_id'])
                elif self.current_user.get('role') == 'leader':
                    from models.user import UserRepository as U3
                    lw_ids = U3.get_leader_workers(self.current_user['username'])
                    if lw_ids:
                        wh.append("r.worker_id IN (" + ','.join(['?'] * len(lw_ids)) + ")")
                        pa.extend(lw_ids)
                    elif self.current_user.get('group_name'):
                        wh.append("r.worker_id IN (SELECT id FROM workers WHERE group_name=?)")
                        pa.append(self.current_user['group_name'])
            # 筛选条件
            if sd:
                wh.append("r.record_date >= ?")
                pa.append(sd)
            if ed:
                wh.append("r.record_date <= ?")
                pa.append(ed)
            if wf and wf != '(全部)':
                wh.append("w.name=?")
                pa.append(wf)
            if pf and pf != '(全部)':
                if ' - ' in pf:
                    mat, proc = pf.split(' - ', 1)
                    wh.append("p.material=? AND p.process_name=?")
                    pa.extend([mat, proc])
            ws = " WHERE " + " AND ".join(wh) if wh else ""
            rows = conn.execute(f"""SELECT r.*, w.name AS worker_name, w.group_name,
                    p.material, p.process_name
                    FROM records r
                    LEFT JOIN workers w ON r.worker_id = w.id
                    LEFT JOIN processes p ON r.process_id = p.id
                    {ws}
                    ORDER BY r.id DESC LIMIT 500""", pa).fetchall()
            for r in rows:
                wage = r['quantity'] * r['unit_price']
                self._tree.insert('', END, values=(
                    r['id'], r['material'], r['process_name'], r['worker_name'],
                    r['group_name'], r['quantity'], f'{YEN}{r["unit_price"]}',
                    f'{YEN}{round(wage, 2)}', r['record_date']
                ))
                self._tree.item(self._tree.get_children()[-1], tags=(str(r['id']),))
            # 更新统计
            from models.record import RecordRepository as RR
            from models.worker import WorkerRepository
            wf_id = None
            if wf and wf != '(全部)':
                for w in WorkerRepository.get_all():
                    if w['name'] == wf:
                        wf_id = w['id']
                        break
            stats = RR.get_stats(start_date=sd if sd else None, end_date=ed if ed else None,
                                worker_filter=wf_id, user=self.current_user)
            t = stats.get('totals', {})
            self._stat_labels['w'].config(text=t.get('w', 0))
            self._stat_labels['q'].config(text=str(t.get('q', 0)))
            self._stat_labels['e'].config(text=f'{YEN}{round(t.get("e", 0), 2)}')
            self._stat_labels['r'].config(text=t.get('r', 0))
        except Exception as e:
            logger.error(f'筛选查询失败: {e}', exc_info=True)
            messagebox.showerror('查询错误', f'筛选时发生错误:\n{e}')
            # 出错时重新加载数据
            self._refresh_table()

    def _reset_filter(self):
        """重置筛选条件"""
        if hasattr(self, '_filter_date_from'):
            self._filter_date_from.delete(0, END)
        if hasattr(self, '_filter_date_to'):
            self._filter_date_to.delete(0, END)
        if hasattr(self, '_filter_worker'):
            self._filter_worker.set('(全部)')
        if hasattr(self, '_filter_process'):
            self._filter_process.set('(全部)')
        self._refresh_table()

    # ── Charts ──
    def _open_chart(self):
        stats = RecordRepository.get_stats()
        gen_report(stats, '生产记录统计')

    def _monthly_summary(self):
        from datetime import date as dt_date
        import calendar as cal_mod
        from tkinter import Toplevel, ttk
        top = Toplevel(self.root)
        top.title('月度汇总')
        top.geometry('700x500')
        top.configure(bg=CARD)
        top.grab_set()
        Label(top, text='选择月份', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(10, 4))
        months = RecordRepository.list_months()
        if not months:
            Label(top, text='暂无数据', bg=CARD, fg='#888').pack()
            return
        cb = ttk.Combobox(top, values=months, state='readonly', width=12,
                          font=('Microsoft YaHei', 11))
        cb.pack(pady=4)
        cb.set(months[0] if months else '')

        def do_report():
            m = cb.get()
            if not m:
                return
            parts = m.split('-')
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                messagebox.showinfo('提示', f'无效的月份格式: {m}')
                return
            y, mo = int(parts[0]), int(parts[1])
            _, ld = cal_mod.monthrange(y, mo)
            stats = RecordRepository.get_stats(start_date=f'{m}-01', end_date=f'{y}-{mo:02d}-{ld:02d}', user=self.current_user)
            gen_report(stats, f'{m} 月度汇总')

        Button(top, text='生成报告', command=do_report, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=14, pady=4, cursor='hand2').pack(pady=6)

        tr = ttk.Treeview(top, columns=('name', 'group', 'qty', 'wage'),
                          show='headings', height=10)
        for col, text, w in [('name', '工人', 100), ('group', '组别', 100),
                              ('qty', '件数', 80), ('wage', '工价', 100)]:
            tr.heading(col, text=text)
            tr.column(col, width=w)
        tr.pack(fill=BOTH, expand=True, padx=10, pady=10)

        def refresh_m():
            tr.delete(*tr.get_children())
            m = cb.get()
            if not m:
                return
            parts = m.split('-')
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                return
            y, mo = int(parts[0]), int(parts[1])
            _, ld = cal_mod.monthrange(y, mo)
            stats = RecordRepository.get_stats(start_date=f'{m}-01', end_date=f'{y}-{mo:02d}-{ld:02d}', user=self.current_user)
            for r in stats.get('by_worker', []):
                tr.insert('', END, values=(r['worker'], r['group_name'], r['q'], round(r['e'], 2)))

        cb.bind('<<ComboboxSelected>>', lambda e: refresh_m())
        if months:
            refresh_m()

        def do_export():
            m = cb.get()
            if not m:
                return
            parts = m.split('-')
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                return
            y, mo = int(parts[0]), int(parts[1])
            _, ld = cal_mod.monthrange(y, mo)
            stats = RecordRepository.get_stats(start_date=f'{m}-01', end_date=f'{y}-{mo:02d}-{ld:02d}', user=self.current_user)
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')], initialfile=f'月度汇总_{m}.xlsx', title='保存月度汇总')
            if not path:
                return
            if export_excel(stats, path, f'{m} 月度汇总'):
                messagebox.showinfo('成功', f'已导出: {path}')

        Button(top, text='导出 Excel', command=do_export, bg=GREEN, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2').pack(pady=(0, 8))

    # ── Dialogs ──
    def _manage_materials(self):
        if not self._check_perm('material_manage'):
            messagebox.showinfo('提示', '您没有管理物料的权限')
            return
        MaterialDialog(self.root)

    def _manage_workers(self):
        if not self._check_perm('worker_manage'):
            messagebox.showinfo('提示', '您没有管理工人的权限')
            return
        WorkerDialog(self.root)

    def _manage_processes(self):
        if not self._check_perm('process_manage'):
            messagebox.showinfo('提示', '您没有管理工序的权限')
            return
        ProcessDialog(self.root)

    def _manage_users(self):
        logger.info('_manage_users 被调用')
        UserDialog(self.root)

    def _manage_permissions(self):
        self._show_permission_dialog()

    def _show_permission_dialog(self):
        from tkinter import Toplevel, Label, Frame, Canvas, Scrollbar, Checkbutton, IntVar, VERTICAL, HORIZONTAL, BOTTOM
        from config import ROLE_NAMES
        top = Toplevel(self.root)
        top.title('权限管理')
        top.geometry('1000x500')
        top.configure(bg=CARD)
        top.grab_set()
        Label(top, text='权限管理', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))
        Label(top, text='点击复选框切换权限', font=('Microsoft YaHei', 9),
              bg=CARD, fg='#888').pack(anchor=W, padx=16)

        canvas = Canvas(top, bg=CARD, highlightthickness=0)
        vsb = Scrollbar(top, orient=VERTICAL, command=canvas.yview)
        hsb = Scrollbar(top, orient=HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        hsb.pack(side=BOTTOM, fill=X)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        frame = Frame(canvas, bg=CARD)
        canvas.create_window((0, 0), window=frame, anchor='nw')
        frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # 获取用户和权限数据
        try:
            users = UserRepository.get_all()
            logger.info(f'权限管理: 加载了 {len(users)} 个用户')
        except Exception as e:
            logger.error(f'加载用户列表失败: {e}')
            Label(top, text=f'加载数据失败: {e}', bg=CARD, fg='red',
                  font=('Microsoft YaHei', 10)).pack(pady=20)
            return

        if not users:
            logger.warning('权限管理: 没有用户可显示')
            Label(top, text='暂无用户数据，请先添加用户', bg=CARD, fg='#888',
                  font=('Microsoft YaHei', 10)).pack(pady=20)
            return

        perm_labels = [
            ('record_add', '添加记录'), ('record_delete', '删除记录'),
            ('record_edit', '编辑记录'), ('material_manage', '管理物料'),
            ('worker_manage', '管理工人'), ('process_manage', '管理工序'),
            ('assignment_manage', '工序分配'), ('chart_view', '查看图表'),
            ('summary_view', '查看汇总'), ('export_excel', '导出Excel'),
            ('user_manage', '用户管理'),
        ]
        perms = [p[0] for p in perm_labels]

        Label(frame, text='用户', bg=CARD, fg=DARK, font=('Microsoft YaHei', 9, 'bold'),
              width=10, anchor='w').grid(row=0, column=0, padx=4, pady=2, sticky='w')
        Label(frame, text='角色', bg=CARD, fg=DARK, font=('Microsoft YaHei', 9, 'bold'),
              width=8, anchor='w').grid(row=0, column=1, padx=4, pady=2, sticky='w')
        for ci, (pk, pl) in enumerate(perm_labels, 2):
            Label(frame, text=pl, bg=CARD, fg='#555', font=('Microsoft YaHei', 8),
                  width=7, anchor='w').grid(row=0, column=ci, padx=2, pady=2)

        self._perm_vars = {}
        for ri, u in enumerate(users, 1):
            un = u['username']
            try:
                Label(frame, text=un, bg=CARD, fg=DARK, font=('Microsoft YaHei', 9),
                      width=10, anchor='w').grid(row=ri, column=0, padx=4, pady=1, sticky='w')
                role_cn = ROLE_NAMES.get(u.get('role', ''), u.get('role', ''))
                Label(frame, text=role_cn, bg=CARD, fg='#555', font=('Microsoft YaHei', 9),
                      width=8, anchor='w').grid(row=ri, column=1, padx=4, pady=1, sticky='w')
                perms_dict = UserRepository.get_permissions(un)
                for ci, pk in enumerate(perms, 2):
                    var = IntVar(value=perms_dict.get(pk, 0))
                    self._perm_vars[(un, pk)] = var
                    def make_cmd(u_name, p_key):
                        return lambda: UserRepository.set_permission(
                            u_name, p_key, self._perm_vars[(u_name, p_key)].get())
                    cb = Checkbutton(frame, variable=var, bg=CARD, command=make_cmd(un, pk))
                    cb.grid(row=ri, column=ci)
            except Exception as e:
                logger.error(f'加载用户 {un} 的权限失败: {e}')

    # ── Calendar ──
    def _show_calendar(self, entry, parent=None):
        import calendar as cal_mod
        from tkinter import Toplevel, Button
        top = Toplevel(self.root)
        top.title('选择日期')
        top.geometry('300x260')
        top.resizable(False, False)
        top.configure(bg=CARD)
        top.grab_set()
        top.transient(parent or self.root)
        xp = self.root.winfo_x() + self.root.winfo_width() // 2 - 150
        yp = self.root.winfo_y() + self.root.winfo_height() // 2 - 130
        top.geometry(f'+{xp}+{yp}')

        now = date.today()
        state = {'y': now.year, 'm': now.month}

        head = Frame(top, bg=CARD)
        head.pack(fill=X, padx=8, pady=(8, 4))
        btn_prev = Button(head, text='‹', bg='#eee', relief='flat',
                          padx=4, cursor='hand2', font=('Microsoft YaHei', 10, 'bold'))
        btn_prev.pack(side=LEFT)
        title_lbl = Label(head, bg=CARD, fg=DARK, font=('Microsoft YaHei', 11, 'bold'))
        title_lbl.pack(side=LEFT, expand=True)
        btn_next = Button(head, text='›', bg='#eee', relief='flat',
                          padx=4, cursor='hand2', font=('Microsoft YaHei', 10, 'bold'))
        btn_next.pack(side=RIGHT)

        grid = Frame(top, bg=CARD)
        grid.pack(padx=8, fill=BOTH, expand=True)
        for ci, d in enumerate(['一', '二', '三', '四', '五', '六', '日']):
            Label(grid, text=d, bg=CARD, fg='#888', font=('Microsoft YaHei', 8),
                  width=4).grid(row=0, column=ci, padx=1, pady=1)

        def rebuild():
            for w in grid.winfo_children():
                if int(w.grid_info()['row']) > 0:
                    w.destroy()
            title_lbl.config(text=f'{state["y"]}年{state["m"]}月')
            cal = cal_mod.monthcalendar(state['y'], state['m'])
            today = date.today()
            for ri, week in enumerate(cal, 1):
                for ci, d in enumerate(week):
                    if d == 0:
                        continue
                    is_today = (state['y'] == today.year and
                                state['m'] == today.month and d == today.day)
                    bg = '#1a73e8' if is_today else 'white'
                    fg = 'white' if is_today else DARK
                    btn = Button(grid, text=str(d), bg=bg, fg=fg,
                                 font=('Microsoft YaHei', 9), relief='flat',
                                 width=4, cursor='hand2',
                                 command=lambda dd=d: [
                                     entry.delete(0, END),
                                     entry.insert(0, f'{state["y"]}-{state["m"]:02d}-{dd:02d}'),
                                     top.destroy()])
                    btn.grid(row=ri, column=ci, padx=1, pady=1)

        def prev():
            if state['m'] == 1:
                state['y'] -= 1
                state['m'] = 12
            else:
                state['m'] -= 1
            rebuild()

        def next_m():
            if state['m'] == 12:
                state['y'] += 1
                state['m'] = 1
            else:
                state['m'] += 1
            rebuild()

        btn_prev.config(command=prev)
        btn_next.config(command=next_m)
        rebuild()

    # ── Logout / Change password ──
    def _logout(self):
        if self._on_logout:
            self._on_logout()

    def _change_pw(self):
        un = self.current_user['username'] if self.current_user else ''
        if not un:
            return
        from tkinter import Toplevel
        cp = Toplevel(self.root)
        cp.title('修改密码')
        cp.geometry('320x230')
        cp.configure(bg=CARD)
        cp.resizable(False, False)
        cp.grab_set()
        cp.transient(self.root)
        xp = self.root.winfo_x() + self.root.winfo_width() // 2 - 160
        yp = self.root.winfo_y() + self.root.winfo_height() // 2 - 115
        cp.geometry(f'+{xp}+{yp}')

        Label(cp, text='修改密码', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(12, 10))
        ff = Frame(cp, bg=CARD)
        ff.pack(padx=24)
        Label(ff, text='用户名：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=0, column=0, sticky=W, pady=3)
        eu = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1)
        eu.insert(0, un)
        eu.config(state='readonly')
        eu.grid(row=0, column=1, pady=3)
        Label(ff, text='旧密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=1, column=0, sticky=W, pady=3)
        eo = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        eo.grid(row=1, column=1, pady=3)
        Label(ff, text='新密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=2, column=0, sticky=W, pady=3)
        en = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        en.grid(row=2, column=1, pady=3)
        Label(ff, text='确认密码：', bg=CARD, font=('Microsoft YaHei', 10)).grid(
            row=3, column=0, sticky=W, pady=3)
        ec = Entry(ff, width=20, font=('Microsoft YaHei', 10), relief='solid', bd=1, show='*')
        ec.grid(row=3, column=1, pady=3)
        err2 = Label(cp, text='', bg=CARD, fg=RED, font=('Microsoft YaHei', 9))
        err2.pack(pady=(4, 0))

        def do_change():
            opw = eo.get().strip()
            npw = en.get().strip()
            cpw = ec.get().strip()
            if not opw or not npw:
                err2.config(text='请填写完整')
                return
            if npw != cpw:
                err2.config(text='两次新密码不一致')
                return
            if len(npw) < 4:
                err2.config(text='新密码至少4位')
                return
            user = UserRepository.get_by_username(un)
            if not user:
                err2.config(text='用户不存在')
                return
            if not _verify_pw(opw, user['password_hash']):
                err2.config(text='旧密码错误')
                return
            UserRepository.update_password(un, npw)
            messagebox.showinfo('成功', '密码修改成功')
            cp.destroy()

        Button(cp, text='确认修改', bg=ACCENT, fg='white',
               font=('Microsoft YaHei', 10, 'bold'), relief='flat',
               padx=20, pady=2, cursor='hand2',
               command=do_change).pack(pady=(6, 0))
        eo.focus()

    # ── Summary page ──
    def _summary_page(self):
        from tkinter import Toplevel, ttk
        from models.record import RecordRepository as RR
        top = Toplevel(self.root)
        top.title('汇总查询')
        top.geometry('800x550')
        top.configure(bg=CARD)
        top.grab_set()
        Label(top, text='汇总查询', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10, 4))

        ff = Frame(top, bg=CARD)
        ff.pack(fill=X, padx=16)
        Label(ff, text='起始日期:', bg=CARD, fg='#555',
              font=('Microsoft YaHei', 9)).pack(side=LEFT)
        e_start = Entry(ff, width=12, font=('Microsoft YaHei', 10),
                        relief='solid', bd=1)
        e_start.bind('<Button-1>', lambda e: self._show_calendar(e_start, parent=top))
        e_start.pack(side=LEFT, padx=(2, 8))
        Label(ff, text='结束日期:', bg=CARD, fg='#555',
              font=('Microsoft YaHei', 9)).pack(side=LEFT)
        e_end = Entry(ff, width=12, font=('Microsoft YaHei', 10),
                      relief='solid', bd=1)
        e_end.bind('<Button-1>', lambda e: self._show_calendar(e_end, parent=top))
        e_end.pack(side=LEFT, padx=(2, 8))
        # 自动填入当前月份起止日期
        import calendar as cal_mod
        from datetime import date as dt_date
        today = dt_date.today()
        _, last_day = cal_mod.monthrange(today.year, today.month)
        e_start.delete(0, END)
        e_start.insert(0, f'{today.year}-{today.month:02d}-01')
        e_end.delete(0, END)
        e_end.insert(0, f'{today.year}-{today.month:02d}-{last_day:02d}')

        workers = WorkerRepository.get_all()
        cb_worker = ttk.Combobox(ff, values=['全部'] + [w['name'] for w in workers],
                                 state='readonly', width=10)
        cb_worker.pack(side=LEFT, padx=(4, 4))
        cb_worker.set('全部')

        def do_query():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel - 1]['id']
            stats = RR.get_stats(start_date=sd, end_date=ed, worker_filter=wf, user=self.current_user)
            tr.delete(*tr.get_children())
            for r in stats.get('by_worker', []):
                tr.insert('', END, values=(r['worker'], r['group_name'], r['q'], round(r['e'], 2)))

        Button(ff, text='查询', command=do_query, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2').pack(side=LEFT, padx=(8, 0))

        tr = ttk.Treeview(top, columns=('worker', 'group', 'qty', 'wage'),
                          show='headings', height=12)
        for col, text, w in [('worker', '工人', 120), ('group', '组别', 120),
                              ('qty', '件数', 100), ('wage', '工价', 120)]:
            tr.heading(col, text=text)
            tr.column(col, width=w)
        tr.pack(fill=BOTH, expand=True, padx=16, pady=(8, 4))

        def do_query_table():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel - 1]['id']
            stats = RR.get_stats(start_date=sd, end_date=ed, worker_filter=wf, user=self.current_user)
            tr.delete(*tr.get_children())
            for r in stats.get('by_worker', []):
                tr.insert('', END, values=(r['worker'], r['group_name'], r['q'], round(r['e'], 2)))

        def do_export():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel - 1]['id']
            stats = RR.get_stats(start_date=sd, end_date=ed, worker_filter=wf, user=self.current_user)
            from tkinter import filedialog
            export_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')], initialfile='汇总查询.xlsx', title='保存汇总查询')
            if not export_path:
                return
            title = '汇总查询'
            if sd or ed:
                title += f' ({sd or ""}~{ed or ""})'
            if export_excel(stats, export_path, title):
                messagebox.showinfo('成功', f'已导出: {export_path}')

        def do_chart():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel - 1]['id']
            stats = RR.get_stats(start_date=sd, end_date=ed, worker_filter=wf, user=self.current_user)
            gen_report(stats, '汇总查询结果')

        bf = Frame(top, bg=CARD)
        bf.pack(fill=X, padx=16, pady=(0, 8))
        Button(bf, text='生成图表', command=do_chart, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2').pack(side=LEFT, padx=(0, 6))
        Button(bf, text='导出 Excel', command=do_export, bg=GREEN, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=10, cursor='hand2').pack(side=LEFT)
