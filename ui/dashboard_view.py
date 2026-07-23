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
from ui.dialogs.user_dialog import UserDialog
from ui.dialogs.edit_record_dialog import EditRecordDialog
from ui.dialogs.change_password_dialog import ChangePasswordDialog
from ui.dialogs.permission_dialog import PermissionDialog
from models.record import RecordRepository
from models.database import Database
from models.worker import WorkerRepository
from models.process import ProcessRepository
from models.user import UserRepository
from ui.dialogs.material_dialog import MaterialDialog
from ui.dialogs.worker_dialog import WorkerDialog
from ui.dialogs.process_dialog import ProcessDialog
from utils.logger import logger


def _format_process_display(p: dict) -> str:
    """格式化工序显示文本：编号(名称)-版本 / 工序名"""
    ver = f"-{p.get('material_version', '')}" if p.get('material_version') else ''
    return f"{p['material_code']}({p.get('material_name', '')}){ver} / {p['process_name']}"


# ── 工具函数 ──
def _fmt_process(p):
    """格式化工序显示文本：编号(名称)-版本 / 工序名"""
    ver = f"-{p.get('material_version', '')}" if p.get('material_version') else ''
    return f"{p['material_code']}({p.get('material_name', '')}){ver} / {p['process_name']}"


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
        self._filter_worker = ttk.Combobox(filter_bar, values=[], width=10,
                                            postcommand=self._filter_worker_search)
        self._filter_worker.pack(side=LEFT, padx=(2, 4))
        Label(filter_bar, text='工序', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(4, 0))
        self._filter_process = ttk.Combobox(filter_bar, values=[], width=22,
                                            postcommand=self._filter_process_search)
        self._filter_process.pack(side=LEFT, padx=(2, 4))
        Button(filter_bar, text='查询', bg=PRIMARY, fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2',
               command=self._apply_filter).pack(side=LEFT, padx=(4, 0))
        Button(filter_bar, text='重置', bg='#7f8c8d', fg='white',
               font=('Microsoft YaHei', 9, 'bold'), relief='flat',
               padx=8, cursor='hand2',
               command=self._reset_filter).pack(side=LEFT, padx=(4, 0))
        Label(filter_bar, text='排序', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(side=LEFT, padx=(6, 0))
        self._filter_sort = ttk.Combobox(filter_bar, values=['最新优先', '最早优先'],
                                          state='readonly', width=9)
        self._filter_sort.set('最新优先')
        self._filter_sort.pack(side=LEFT, padx=(2, 4))
        self._filter_sort.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        # ── Record entry form ──
        fm = Frame(main, bg=CARD, highlightbackground='#ddd',
                   highlightthickness=1, padx=14, pady=10)
        fm.pack(fill=X, pady=(0, 10))
        Label(fm, text='添加记录', font=('Microsoft YaHei', 11, 'bold'),
              bg=CARD, fg=DARK).pack(anchor=W)
        row = Frame(fm, bg=CARD)
        row.pack(fill=X, pady=(6, 0))

        fid = Frame(row, bg=CARD)
        fid.pack(side=LEFT, padx=(0, 8))
        Label(fid, text='ID（留空自动填充）', bg=CARD, fg='#666',
              font=('Microsoft YaHei', 9)).pack(anchor=W, padx=(2, 0))
        self.e_id = Entry(fid, width=8, font=('Microsoft YaHei', 11),
                          relief='solid', bd=1, justify=CENTER)
        self.e_id.pack()

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
                    ('worker', '姓名', 70), ('group', '班组', 70), ('qty', '件数', 60),
                    ('price', '工价', 60), ('wage', '总价', 70), ('date', '日期', 100)]
        for col, text, w in col_defs:
            self._tree.heading(col, text=text)
            self._tree.column(col, width=w, anchor=CENTER)
        self._tree.pack(side=LEFT, fill=BOTH, expand=True)
        vsb = Scrollbar(tree_frame, orient=VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)

        # 绑定双击编辑事件（使用 tree 级别绑定，确保始终有效）
        self._tree.bind('<Double-1>', self._edit_record)

        # ── Bottom buttons ──
        bottom = Frame(main, bg=BG)
        bottom.pack(fill=X, pady=(4, 0))
        self._make_btn(bottom, '📊 生成图表报告', self._open_chart, 'chart_view', PRIMARY)
        self._make_btn(bottom, '📅 月度汇总', self._monthly_summary, 'monthly_view', GREEN)

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
            self._status_label = Label(bt, text=f'当前用户: {dn} ({un}) - {role_cn}', bg='white', fg='#888',
                  font=('Microsoft YaHei', 8))
        self._status_label.pack(side=LEFT, padx=12)
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
        if wid in self._worker_procs and self._worker_procs[wid]:
            procs = self._worker_procs[wid]
            self.cb_process['values'] = [
                _format_process_display(p) for p in procs
            ]
        else:
            self.cb_process['values'] = ['(暂无可用工序)']
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
                self.price_label.config(text=f'工价: {YEN}{procs[sel]["unit_price"]}')

    # ── CRUD operations ──
    def _do_add(self):
        # 获取自定义ID（可选）
        id_s = self.e_id.get().strip()
        custom_id = None
        if id_s:
            try:
                custom_id = int(id_s)
                if custom_id < 1:
                    messagebox.showinfo('提示', 'ID必须为正整数')
                    return
            except ValueError:
                messagebox.showinfo('提示', 'ID必须为正整数（留空则自动生成）')
                return

        wid = self.cb_worker.current()
        pid = self.cb_process.current()
        qty_s = self.e_qty.get().strip()
        d = self.e_date.get().strip()
        if wid < 0 or pid < 0 or not qty_s:
            messagebox.showinfo('提示', '请选择工人、工序并填写件数')
            return
        try:
            qty_f = float(qty_s)
            if qty_f != int(qty_f):
                messagebox.showinfo('提示', '件数必须为正整数')
                return
            qty = int(qty_f)
        except ValueError:
            messagebox.showinfo('提示', '件数必须为正整数')
            return
        if qty < 1:
            messagebox.showinfo('提示', '件数必须大于0')
            return
        widsel = self._worker_ids[wid]
        proc_id = 0
        price = 0
        if widsel in self._worker_procs and pid < len(self._worker_procs[widsel]):
            proc = self._worker_procs[widsel][pid]
            proc_id = proc['id']
            price = proc['unit_price']

        ok = False
        if custom_id:
            ok = RecordRepository.add_with_id(custom_id, widsel, proc_id, qty, price, d)
        else:
            ok = RecordRepository.add(widsel, proc_id, qty, price, d)

        if ok:
            self.e_id.delete(0, END)
            self.e_qty.delete(0, END)
            self.refresh()
            messagebox.showinfo('成功', '记录已添加')
        else:
            messagebox.showerror('错误', '添加失败，ID可能已被占用')

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
        """双击表格行编辑记录 — 委托给 EditRecordDialog"""
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
        try:
            EditRecordDialog(
                parent_root=self.root,
                record_id=int(vals[0]),
                current_user=self.current_user,
                on_save_callback=self.refresh
            )
        except PermissionError:
            pass

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

        # Load all processes (worker-process assignment removed)
        self._worker_ids = []
        self._worker_procs = {}
        all_procs = ProcessRepository.get_all()
        for w in all_workers:
            self._worker_ids.append(w['id'])
            # Show all processes for every worker
            self._worker_procs[w['id']] = all_procs

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
                    self._on_worker_sel(None)  # 触发工序下拉框更新
                else:
                    self.cb_worker.config(state='readonly')
            else:
                self.cb_worker.config(state='readonly')

        # 填充筛选栏下拉框
        if hasattr(self, '_filter_worker'):
            names = [w['name'] for w in all_workers]
            self._filter_worker_names = names
            self._filter_worker['values'] = ['(全部)'] + names
            if not self._filter_worker.get():
                self._filter_worker.set('(全部)')
        if hasattr(self, '_filter_process'):
            proc_names = sorted(set(
                _fmt_process(p) for p in all_procs
            ))
            self._filter_proc_names = proc_names
            self._filter_process['values'] = ['(全部)'] + proc_names
            if not self._filter_process.get():
                self._filter_process.set('(全部)')

        # Refresh table
        self._refresh_table()

    def _filter_process_search(self, ev=None):
        """工序下拉搜索过滤"""
        kw = self._filter_process.get()
        names = getattr(self, '_filter_proc_names', [])
        if not kw or kw == '(全部)':
            self._filter_process['values'] = ['(全部)'] + names
        else:
            matched = ['(全部)'] + [n for n in names if kw.lower() in n.lower()]
            self._filter_process['values'] = matched

    def _filter_worker_search(self, ev=None):
        """工人下拉搜索过滤"""
        kw = self._filter_worker.get()
        names = getattr(self, '_filter_worker_names', [])
        if not kw or kw == '(全部)':
            self._filter_worker['values'] = ['(全部)'] + names
        else:
            matched = ['(全部)'] + [n for n in names if kw.lower() in n.lower()]
            self._filter_worker['values'] = matched

    def _show_empty_hint(self, tree, text='暂无数据'):
        """在 TreeView 中显示灰色空数据提示"""
        tree.delete(*tree.get_children())
        cols = tree.cget('columns')
        if isinstance(cols, str):
            cols = cols.split()
        n_cols = len(cols) if cols else 1
        # 第一条为0避免int()转换错误，其余为空字符串
        tree.insert('', 'end', values=['0'] + [''] * (n_cols - 1),
                    tags=('empty_hint',))
        # 在第一个可见单元格显示提示文字（覆盖ID列后的第一列）
        tree.tag_configure('empty_hint', foreground='#999999', font=('Microsoft YaHei', 9),
                           anchor='center')

    def _get_order_sql(self, default_desc=True):
        """根据排序选择器返回 ORDER BY 子句"""
        sort = getattr(self, '_filter_sort', None)
        if sort and sort.get() == '最早优先':
            return 'ORDER BY r.record_date ASC, r.id ASC'
        if default_desc:
            return 'ORDER BY r.id DESC'
        return ''

    def _refresh_table(self):
        if not self._tree:
            return
        self._tree.delete(*self._tree.get_children())
        records = RecordRepository.get_all(self.current_user, order_sql=self._get_order_sql())
        for r in records[:200]:
            wage = r['quantity'] * r['unit_price']
            # 格式化物料显示
            from models.material import MaterialRepository
            mat_display = r.get('material_code', '') or ''
            mat = MaterialRepository.get_by_code(r.get('material_code', '')) if r.get('material_code') else None
            if mat:
                ver = f"-{mat['version']}" if mat['version'] else ''
                mat_display = f"{mat['code']}({mat['name']}){ver}"
            item = self._tree.insert('', END, values=(
                r['id'], mat_display, r['process_name'], r['worker_name'],
                r['group_name'], r['quantity'], f'{YEN}{r["unit_price"]}',
                f'{YEN}{round(wage, 2)}', r['record_date']
            ))
            # 存储完整记录数据到 tags 中，供编辑时使用
            self._tree.item(item, tags=(str(r['id']),))

        if not records:
            self._tree.delete(*self._tree.get_children())
            self._tree.insert('', END, values=(0, '暂无匹配的生产记录', '', '', '', '', '', '', ''))
            self._tree.tag_configure('empty_hint', foreground='#999', font=('Microsoft YaHei', 9))
            self._tree.item(self._tree.get_children()[0], tags=('empty_hint',))

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
            # 使用 PermissionService 统一处理数据权限过滤
            from services.permission_service import PermissionService
            perm_where, perm_params = PermissionService.build_worker_filter_clause(self.current_user, 'r')
            if perm_where:
                wh.append(perm_where)
                pa.extend(perm_params)
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
                if ' / ' in pf:
                    mat_part, proc = pf.split(' / ', 1)
                    # 物料部分格式：编号(名称)-版本，提取编号
                    mat_code = mat_part.split('(')[0].strip()
                    wh.append("p.material_code=? AND p.process_name=?")
                    pa.extend([mat_code, proc])
            ws = " WHERE " + " AND ".join(wh) if wh else ""
            rows = conn.execute(f"""SELECT r.*, w.name AS worker_name, w.group_name,
                    p.material_code, p.process_name
                    FROM records r
                    LEFT JOIN workers w ON r.worker_id = w.id
                    LEFT JOIN processes p ON r.process_id = p.id
                    {ws}
                    {self._get_order_sql()} LIMIT 500""", pa).fetchall()
            for r in rows:
                wage = r['quantity'] * r['unit_price']
                # 获取物料名称用于显示
                from models.material import MaterialRepository
                mat = MaterialRepository.get_by_code(r['material_code']) if r['material_code'] else None
                mat_display = r['material_code'] or ''
                if mat:
                    ver = f"-{mat['version']}" if mat['version'] else ''
                    mat_display = f"{mat['code']}({mat['name']}){ver}"
                self._tree.insert('', END, values=(
                    r['id'], mat_display, r['process_name'], r['worker_name'],
                    r['group_name'], r['quantity'], f'{YEN}{r["unit_price"]}',
                    f'{YEN}{round(wage, 2)}', r['record_date']
                ))
                self._tree.item(self._tree.get_children()[-1], tags=(str(r['id']),))
            if not rows:
                self._tree.delete(*self._tree.get_children())
                self._tree.insert('', END, values=(0, '筛选无匹配的记录', '', '', '', '', '', '', ''))
                self._tree.tag_configure('empty_hint', foreground='#999', font=('Microsoft YaHei', 9))
                self._tree.item(self._tree.get_children()[0], tags=('empty_hint',))
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
        if not self._check_perm('chart_view'):
            messagebox.showinfo('提示', '您没有查看图表的权限')
            return
        stats = RecordRepository.get_stats(user=self.current_user)
        gen_report(stats, '生产记录统计')

    def _monthly_summary(self):
        if not self._check_perm('monthly_view'):
            messagebox.showinfo('提示', '您没有查看月度汇总的权限')
            return
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
        for col, text, w in [('name', '工人', 100), ('group', '班组', 100),
                              ('qty', '件数', 80), ('wage', '总价', 100)]:
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
            if not stats.get('by_worker', []):
                tr.delete(*tr.get_children())
                tr.insert('', END, values=('该月暂无生产记录', '', '', ''))
                tr.tag_configure('empty_hint', foreground='#999', font=('Microsoft YaHei', 9))
                tr.item(tr.get_children()[0], tags=('empty_hint',))

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
        WorkerDialog(self.root, self.current_user)

    def _manage_processes(self):
        if not self._check_perm('process_manage'):
            messagebox.showinfo('提示', '您没有管理工序的权限')
            return
        ProcessDialog(self.root)

    def _manage_users(self):
        logger.info('_manage_users 被调用')
        UserDialog(self.root)
        # 对话框关闭后，刷新当前用户信息（可能用户名被改了）
        if self.current_user:
            from models.user import UserRepository
            refreshed = UserRepository.get_by_username(self.current_user['username'])
            if refreshed:
                self.current_user = refreshed
            # 刷新底部状态栏
            self._refresh_status_bar()

    def _manage_permissions(self):
        self._show_permission_dialog()

    def _show_permission_dialog(self):
        """权限管理 — 委托给 PermissionDialog"""
        PermissionDialog(self.root)

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

    def _refresh_status_bar(self):
        """更新底部状态栏的当前用户信息"""
        if hasattr(self, '_status_label') and self.current_user:
            un = self.current_user.get('username', '')
            dn = self.current_user.get('display_name', '')
            role_en = self.current_user.get('role', '')
            from config import ROLE_NAMES
            role_cn = ROLE_NAMES.get(role_en, role_en)
            self._status_label.config(text=f'当前用户: {dn} ({un}) - {role_cn}')

    def _change_pw(self):
        """修改密码 — 委托给 ChangePasswordDialog"""
        if not self.current_user:
            return
        ChangePasswordDialog(self.root, self.current_user)

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
                                 width=10)
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
        for col, text, w in [('worker', '工人', 120), ('group', '班组', 120),
                              ('qty', '件数', 100), ('wage', '总价', 120)]:
            tr.heading(col, text=text)
            tr.column(col, width=w, anchor='center')
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
            if not stats.get('by_worker', []):
                tr.delete(*tr.get_children())
                tr.insert('', END, values=('该时间段无生产记录', '', '', ''))
                tr.tag_configure('empty_hint', foreground='#999', font=('Microsoft YaHei', 9))
                tr.item(tr.get_children()[0], tags=('empty_hint',))

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
        
        # 打开时自动查询
        top.after(100, do_query)
