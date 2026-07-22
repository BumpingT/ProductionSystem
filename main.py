"""
生产管理系统 ProductionSystem
"""
import sqlite3, os, sys, webbrowser, tempfile, json, shutil, calendar
import hashlib, secrets, base64
from datetime import date, timedelta
from tkinter import *
from tkinter import ttk, messagebox

# ── 使用新架构模块 ──
from config import DB_PATH, ECHARTS_PATH, LOGIN_CRED_PATH, YEN, ALL_PERMS
from config import BG, CARD, PRIMARY, ACCENT, GREEN, RED, DARK
from utils.auth import hash_password as _hash_pw, verify_password as _verify_pw
from utils.auth import save_credential as _save_cred, load_credential as _load_cred
from utils.auth import clear_credential as _clear_cred

def _rp(rel):
    try: base = sys._MEIPASS
    except: base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

def _set_placeholder(entry, text):
    entry._ph_text = text
    entry.insert(0, text)
    entry.config(fg='#999999')
    def _in(e):
        if entry.get() == entry._ph_text:
            entry.delete(0, END); entry.config(fg='#333333')
    def _out(e):
        if not entry.get().strip():
            entry.insert(0, entry._ph_text); entry.config(fg='#999999')
    entry.bind('<FocusIn>', _in, '+'); entry.bind('<FocusOut>', _out, '+')


# ── Database ──

from models.database import Database
from models.record import RecordRepository
from models.user import UserRepository
from services.material_service import MaterialService
from services.worker_service import WorkerService
from services.process_service import ProcessService
from services.auth_service import AuthService
from services.stats_service import StatsService

init_db = Database.init_db
get_conn = Database.get_conn
get_materials = MaterialService.get_all
add_material = MaterialService.add
update_material = MaterialService.update
delete_material = MaterialService.delete
get_workers = WorkerService.get_all
add_worker = WorkerService.add
delete_worker = WorkerService.delete
get_processes = ProcessService.get_all
add_process = ProcessService.add
delete_process = ProcessService.delete
get_worker_processes = ProcessService.get_worker_processes
assign_worker_process = ProcessService.assign_worker
unassign_worker_process = ProcessService.unassign_worker

# ── 仍在 main.py 中使用的函数 ──
get_users = UserRepository.get_all
get_user_by_worker_id = UserRepository.get_by_worker_id
add_user = UserRepository.add
update_user_pw = UserRepository.update_password
update_user_display = UserRepository.update_profile
delete_user = UserRepository.delete
get_user_perms = UserRepository.get_permissions
set_user_perm = UserRepository.set_permission
update_worker = WorkerService.update
add_record = RecordRepository.add
update_record = RecordRepository.update
delete_record = RecordRepository.delete
get_all_records = RecordRepository.get_all
get_stats = StatsService.get_summary
list_months = RecordRepository.list_months

# ── 服务层 ──
from services.chart_service import _chart_html, gen_report
from services.export_service import export_excel

# ── 基本路径 ──
if getattr(sys, "frozen", False): _BASE = os.path.dirname(sys.executable)
else: _BASE = os.path.dirname(os.path.abspath(__file__))

# ── UI 模块（显式导入确保 PyInstaller 打包）──
from ui.widgets.crud_dialog_base import CrudDialogBase
from ui.dialogs.material_dialog import MaterialDialog
from ui.dialogs.worker_dialog import WorkerDialog
from ui.dialogs.process_dialog import ProcessDialog


class App:
    def __init__(self):
        self.root = Tk()
        self.root.title('生产管理系统')
        self.root.geometry('1200x750')
        self.root.configure(bg=BG)
        self.root.withdraw()
        self.current_user = None
        self.user_perms = {}
        self.show_login()
    
    # ── Permission helpers ──
    def _check_perm(self, perm_key):
        if not self.current_user:
            return False
        if self.current_user.get('role') == 'admin':
            return True
        return bool(self.user_perms.get(perm_key, 0))
    
    def _apply_permissions(self):
        """Enable/disable buttons based on permissions"""
        for widget_name, perm_key in self._perm_widgets:
            for child in self.root.winfo_children():
                self._apply_to_child(child, widget_name, perm_key)
    
    def _apply_to_child(self, parent, widget_name, perm_key):
        if hasattr(parent, '_perm_name') and parent._perm_name == widget_name:
            state = 'normal' if self._check_perm(perm_key) else 'disabled'
            try: parent.config(state=state)
            except: pass
        for child in parent.winfo_children():
            self._apply_to_child(child, widget_name, perm_key)
    
    # ── Login ──
    def show_login(self):
        top = Toplevel(self.root)
        top.title('生产管理系统 登录')
        top.geometry('340x320')
        top.configure(bg=CARD); top.resizable(False, False)
        top.grab_set()
        
        Label(top, text='生产管理系统', font=('Microsoft YaHei',16,'bold'), bg=CARD, fg=PRIMARY).pack(pady=(24,4))
        Label(top, text='请输入账号密码', font=('Microsoft YaHei',9), bg=CARD, fg='#888').pack(pady=(0,12))
        
        f = Frame(top, bg=CARD); f.pack(padx=24)
        Label(f, text='用户名：', bg=CARD, fg='#555', font=('Microsoft YaHei',10)).pack(anchor=W)
        un_entry = Entry(f, width=25, relief='solid', font=('Microsoft YaHei',10), bd=1)
        un_entry.pack(pady=(2,8))
        Label(f, text='密码：', bg=CARD, fg='#555', font=('Microsoft YaHei',10)).pack(anchor=W)
        pw_entry = Entry(f, width=25, relief='solid', font=('Microsoft YaHei',10), show='*', bd=1)
        pw_entry.pack(pady=(2,6))
        
        cred_var = IntVar()
        rf = Frame(f, bg=CARD); rf.pack(fill=X)
        Checkbutton(rf, text='记住密码', variable=cred_var, bg=CARD, font=('Microsoft YaHei',9)).pack(side=LEFT)
        Label(rf, text='默认: admin/admin123', bg=CARD, fg='#999', font=('Microsoft YaHei',8)).pack(side=RIGHT)
        
        def do_login():
            un = un_entry.get().strip(); pw = pw_entry.get()
            if not un or not pw: messagebox.showinfo('提示','请输入用户名和密码'); return
            user = AuthService.login(un, pw)
            if not user:
                messagebox.showerror('错误','用户名或密码错误'); return
            self.current_user = user
            self.user_perms = get_user_perms(un)
            if cred_var.get(): _save_cred(un, pw)
            else: _clear_cred()
            top.destroy()
            self.root.deiconify()
            self.build_ui()
            self.refresh()
            self._apply_permissions()
        
        Button(f, text='登录', bg=PRIMARY, fg='white', font=('Microsoft YaHei',11,'bold'),
               relief='flat', padx=8, pady=4, cursor='hand2', command=do_login).pack(fill=X, pady=(8,0))
        
        # Load saved credentials
        cred = _load_cred()
        if cred:
            un_entry.insert(0, cred.get('u',''))
            pw_entry.insert(0, cred.get('p',''))
            cred_var.set(1)
        
        un_entry.focus()
        self.root.bind('<Return>', lambda e: do_login())
        self._login_top = top
        self.root.wait_window(top)
    
    # ── Main UI ──
    def build_ui(self):
        # Header
        hdr = Frame(self.root, bg=PRIMARY, height=64); hdr.pack(fill=X); hdr.pack_propagate(False)
        Label(hdr, text='生产记录管理系统', fg='white', bg=PRIMARY, font=('Microsoft YaHei',16,'bold')).pack(padx=24, pady=(10,0), anchor=W)
        Label(hdr, text='工人 · 工序 · 产量 · 工资 · 动态图表', fg='#b0c4de', bg=PRIMARY, font=('Microsoft YaHei',9)).pack(padx=24, pady=(0,8), anchor=W)
        
        main = Frame(self.root, bg=BG); main.pack(fill=BOTH, expand=True, padx=12, pady=(10,8))
        
        # Toolbar
        tb = Frame(main, bg=CARD); tb.pack(fill=X, pady=(0,8))
        self._perm_widgets = []
        
        def make_btn(tb, text, cmd, perm, bg_color):
            btn = Button(tb, text=text, command=cmd, bg=bg_color, fg='white',
                        font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, pady=3, cursor='hand2')
            btn.pack(side=LEFT, padx=(0,6))
            btn._perm_name = text
            self._perm_widgets.append((text, perm))
            return btn
        
        make_btn(tb, '管理物料', self.manage_materials, 'material_manage', PRIMARY)
        make_btn(tb, '管理工人', self.manage_workers, 'worker_manage', PRIMARY)
        make_btn(tb, '管理工序', self.manage_processes, 'process_manage', PRIMARY)
        make_btn(tb, '汇总查询', self.summary_page, 'summary_view', GREEN)
        # Admin-only buttons - hidden for non-admin
        if self.current_user and self.current_user.get('role') == 'admin':
            make_btn(tb, '用户管理', self.manage_users, 'user_manage', RED)
            make_btn(tb, '权限管理', self.manage_permissions, 'user_manage', GREEN)
        
        # Record entry form
        fm = Frame(main, bg=CARD, highlightbackground='#ddd', highlightthickness=1, padx=14, pady=10)
        fm.pack(fill=X, pady=(0,10))
        Label(fm, text='添加记录', font=('Microsoft YaHei',11,'bold'), bg=CARD, fg=DARK).pack(anchor=W)
        row = Frame(fm, bg=CARD); row.pack(fill=X, pady=(6,0))
        
        fi = Frame(row, bg=CARD); fi.pack(side=LEFT, padx=(0,8))
        Label(fi, text='ID', bg=CARD, fg='#666', font=('Microsoft YaHei',9)).pack(anchor=W, padx=(2,0))
        e_id = Entry(fi, width=6, font=('Microsoft YaHei',11), relief='solid', bd=1, justify=CENTER)
        e_id.pack(); _set_placeholder(e_id, '留空自动')
        
        fw = Frame(row, bg=CARD); fw.pack(side=LEFT, padx=(0,8))
        Label(fw, text='选择工人', bg=CARD, fg='#666', font=('Microsoft YaHei',9)).pack(anchor=W, padx=(2,0))
        self.cb_worker = ttk.Combobox(fw, width=12, font=('Microsoft YaHei',10), state='readonly'); self.cb_worker.pack()
        
        fp = Frame(row, bg=CARD); fp.pack(side=LEFT, padx=(0,8))
        Label(fp, text='选择工序', bg=CARD, fg='#666', font=('Microsoft YaHei',9)).pack(anchor=W, padx=(2,0))
        cb_process = ttk.Combobox(fp, width=18, font=('Microsoft YaHei',10), state='readonly'); cb_process.pack()
        
        fq = Frame(row, bg=CARD); fq.pack(side=LEFT, padx=(0,8))
        Label(fq, text='件数', bg=CARD, fg='#666', font=('Microsoft YaHei',9)).pack(anchor=W, padx=(2,0))
        e_qty = Entry(fq, width=8, font=('Microsoft YaHei',11), relief='solid', bd=1, justify=CENTER)
        e_qty.pack()
        
        fd = Frame(row, bg=CARD); fd.pack(side=LEFT, padx=(0,8))
        Label(fd, text='日期', bg=CARD, fg='#666', font=('Microsoft YaHei',9)).pack(anchor=W, padx=(2,0))
        e_date = Entry(fd, width=12, font=('Microsoft YaHei',11), relief='solid', bd=1, justify=CENTER)
        e_date.pack(); e_date.insert(0, date.today().isoformat())
        e_date.bind('<Button-1>', lambda e: self.show_calendar(e_date))
        
        price_label = Label(row, text='', bg=CARD, fg=ACCENT, font=('Microsoft YaHei',10,'bold'))
        price_label.pack(side=LEFT, padx=(4,8))  # Will show unit price
        
        def on_worker_sel(ev):
            sel = self.cb_worker.current()
            if sel < 0: return
            wid = self._worker_ids[sel] if hasattr(self, '_worker_ids') and sel < len(self._worker_ids) else 0
            if hasattr(self, '_worker_procs') and wid in self._worker_procs:
                procs = self._worker_procs[wid]
                cb_process['values'] = [f"{p['material']} - {p['process_name']}" for p in procs]
            else:
                cb_process['values'] = []
            cb_process.set('')
        
        def on_process_sel(ev):
            sel = cb_process.current()
            if sel < 0: return
            wid = self.cb_worker.current()
            if wid >= 0 and hasattr(self, '_worker_ids') and wid < len(self._worker_ids):
                widsel = self._worker_ids[wid]
                procs = self._worker_procs.get(widsel, [])
                if sel < len(procs):
                    price_label.config(text=f"单价: {YEN}{procs[sel]['unit_price']}")
        
        self.cb_worker.bind('<<ComboboxSelected>>', on_worker_sel)
        cb_process.bind('<<ComboboxSelected>>', on_process_sel)
        
        def do_add():
            wid = self.cb_worker.current()
            pid = self.cb_process.current()
            qty_s = e_qty.get().strip()
            d = e_date.get().strip()
            if wid < 0 or pid < 0 or not qty_s: messagebox.showinfo('提示','请选择工人、工序并填写件数'); return
            try: qty = float(qty_s)
            except: messagebox.showinfo('提示','件数必须为数字'); return
            widsel = self._worker_ids[wid]
            proc_id = 0; price = 0
            if widsel in self._worker_procs and pid < len(self._worker_procs[widsel]):
                proc = self._worker_procs[widsel][pid]
                proc_id = proc['id']
                price = proc['unit_price']
            if add_record(widsel, proc_id, qty, price, d):
                e_qty.delete(0, END); self.refresh(); messagebox.showinfo('成功','记录已添加')
            else: messagebox.showerror('错误','添加失败')
        
        btn_frame = Frame(row, bg=CARD); btn_frame.pack(side=LEFT)
        Button(btn_frame, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei',9,'bold'),
               relief='flat', padx=10, pady=2, cursor='hand2', command=do_add).pack()
        
        # Delete button
        del_frame = Frame(row, bg=CARD); del_frame.pack(side=LEFT, padx=(4,0))
        btn_del = Button(del_frame, text='删除选中', bg=RED, fg='white', font=('Microsoft YaHei',9,'bold'),
                        relief='flat', padx=10, pady=2, cursor='hand2', command=self.delete_selected)
        btn_del.pack()
        btn_del._perm_name = '删除记录'
        self._perm_widgets.append(('删除记录', 'record_delete'))

        # Edit button
        edit_frame = Frame(row, bg=CARD); edit_frame.pack(side=LEFT, padx=(4,0))
        btn_edit = Button(edit_frame, text='编辑选中', bg='#2980b9', fg='white', font=('Microsoft YaHei',9,'bold'),
                         relief='flat', padx=10, pady=2, cursor='hand2', command=self._edit_selected)
        btn_edit.pack()
        btn_edit._perm_name = '编辑记录'
        self._perm_widgets.append(('编辑记录', 'record_edit'))
        
        # Stats bar
        stats_bar = Frame(main, bg='white', relief='solid', bd=1); stats_bar.pack(fill=X, pady=(0,6))
        self._stat_labels = {}
        for key, label in [('w','工人数'),('q','总产量'),('e','总工价'),('r','记录数')]:
            cell = Frame(stats_bar, bg='white'); cell.pack(side=LEFT, expand=True, padx=8, pady=6)
            Label(cell, text=label, bg='white', fg='#888', font=('Microsoft YaHei',8)).pack()
            self._stat_labels[key] = Label(cell, text='0', bg='white', fg=DARK, font=('Microsoft YaHei',14,'bold'))
            self._stat_labels[key].pack()
        
        # Tree table
        tree_frame = Frame(main); tree_frame.pack(fill=BOTH, expand=True)
        tr = ttk.Treeview(tree_frame, columns=('id','material','process','worker','group','qty','price','wage','date'),
                          show='headings', height=12)
        for col, text, w in [('id','ID',40),('material','物料',80),('process','工序',100),('worker','姓名',70),
                            ('group','组别',70),('qty','件数',60),('price','单价',60),('wage','工资',70),('date','日期',100)]:
            tr.heading(col, text=text); tr.column(col, width=w, anchor='center' if col in ('id','qty','price','wage') else 'w')
        tr.pack(side=LEFT, fill=BOTH, expand=True)
        vsb = Scrollbar(tree_frame, orient=VERTICAL, command=tr.yview); tr.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        tr.bind('<Double-1>', self._on_tree_double_click)
        self._tree = tr
        
        # Bottom buttons
        bottom = Frame(main, bg=BG); bottom.pack(fill=X, pady=(4,0))
        Button(bottom, text='📊 生成图表报告', command=self.open_chart, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT, padx=(0,6))
        Button(bottom, text='📅 月度汇总', command=self.monthly_summary, bg=GREEN, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT)
        Button(bottom, text='📎 导出表格', command=self._export_table, bg='#2980b9', fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT, padx=(6,0))
        
        # Bottom status bar
        bt = Frame(self.root, bg='white', highlightbackground='#ddd', highlightthickness=1)
        bt.pack(fill=X)
        if self.current_user:
            un = self.current_user.get('username','')
            dn = self.current_user.get('display_name','')
            Label(bt, text=f'当前用户: {dn} ({un})', bg='white', fg='#888',
                  font=('Microsoft YaHei',8)).pack(side=LEFT, padx=12)
        Button(bt, text='修改密码', bg='#2980b9', fg='white', font=('Microsoft YaHei',9,'bold'),
               relief='flat', padx=10, pady=2, cursor='hand2', command=self._change_pw).pack(side=RIGHT, padx=(4,4))
        Button(bt, text='退出登录', bg=DARK, fg='white', font=('Microsoft YaHei',9,'bold'),
               relief='flat', padx=10, pady=2, cursor='hand2', command=self._logout).pack(side=RIGHT, padx=(4,4))
    
    def _logout(self):
        if messagebox.askyesno('确认', '确定退出登录？'):
            self.root.withdraw()
            self.current_user = None
            self.user_perms = {}
            for w in self.root.winfo_children():
                w.destroy()
            self.show_login()
    
    def _change_pw(self):
        un = self.current_user['username'] if self.current_user else ''
        if not un: return
        cp = Toplevel(self.root); cp.title('修改密码'); cp.geometry('320x230')
        cp.configure(bg=CARD); cp.resizable(False, False); cp.grab_set(); cp.transient(self.root)
        xp = self.root.winfo_x()+self.root.winfo_width()//2-160
        yp = self.root.winfo_y()+self.root.winfo_height()//2-115
        cp.geometry(f'+{xp}+{yp}')
        Label(cp, text='修改密码', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(pady=(12,10))
        ff = Frame(cp, bg=CARD); ff.pack(padx=24)
        Label(ff, text='用户名：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=0,column=0,sticky=W,pady=3)
        eu = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1)
        eu.insert(0, un); eu.config(state='readonly'); eu.grid(row=0,column=1,pady=3)
        Label(ff, text='旧密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=1,column=0,sticky=W,pady=3)
        eo = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*')
        eo.grid(row=1,column=1,pady=3)
        Label(ff, text='新密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=2,column=0,sticky=W,pady=3)
        en = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*')
        en.grid(row=2,column=1,pady=3)
        Label(ff, text='确认密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=3,column=0,sticky=W,pady=3)
        ec = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*')
        ec.grid(row=3,column=1,pady=3)
        err2 = Label(cp, text='', bg=CARD, fg=RED, font=('Microsoft YaHei',9))
        err2.pack(pady=(4,0))
        def do_change():
            opw = eo.get().strip(); npw = en.get().strip(); cpw = ec.get().strip()
            if not opw or not npw: err2.config(text='请填写完整'); return
            if npw != cpw: err2.config(text='两次新密码不一致'); return
            if len(npw) < 4: err2.config(text='新密码至少4位'); return
            user = UserRepository.get_by_username(un)
            if not user: err2.config(text='用户不存在'); return
            if not _verify_pw(opw, user['password_hash']): err2.config(text='旧密码错误'); return
            UserRepository.update_password(un, npw)
            messagebox.showinfo('成功', '密码修改成功'); cp.destroy()
        Button(cp, text='确认修改', bg=ACCENT, fg='white', font=('Microsoft YaHei',10,'bold'),
               relief='flat', padx=20, pady=2, cursor='hand2', command=do_change).pack(pady=(6,0))
        eo.focus()
    
    def refresh(self):
        # Load workers & processes for form
        self._worker_ids = []
        self._worker_procs = {}
        for w in get_workers():
            self._worker_ids.append(w['id'])
            procs = []
            for p in get_processes():
                wp = get_worker_processes(w['id'])
                if p['id'] in wp or True:
                    procs.append(p)
            self._worker_procs[w['id']] = procs
        
        # Update worker combobox
        if hasattr(self, 'cb_worker'):
            self.cb_worker['values'] = [w['name'] for w in get_workers()]
        
        # Refresh table
        self._refresh_table()
    
    def _refresh_table(self):
        tr = self._tree
        tr.delete(*tr.get_children())
        records = get_all_records(self.current_user)
        for r in records[:200]:
            wage = r['quantity'] * r['unit_price']
            tr.insert('', END, values=(r['id'],r['material'],r['process_name'],r['worker_name'],
                                       r['group_name'],r['quantity'],f'{YEN}{r["unit_price"]}',
                                       f'{YEN}{round(wage,2)}',r['record_date']))
    
    def delete_selected(self):
        sel = self._tree.selection()
        if not sel: return
        if not messagebox.askyesno('确认','确定删除选中的记录？'): return
        for item in sel:
            vals = self._tree.item(item, 'values')
            if vals: delete_record(int(vals[0]))
        self.refresh()

    def _on_tree_double_click(self, event):
        """双击表格行触发编辑"""
        self._edit_selected()

    def _edit_selected(self):
        """编辑选中的记录"""
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo('提示', '请先选中一条记录')
            return
        if not self._check_perm('record_edit') and self.current_user.get('role') != 'admin':
            messagebox.showinfo('提示', '没有编辑权限')
            return
        vals = self._tree.item(sel[0], 'values')
        if not vals:
            return
        rid = int(vals[0])
        # 获取当前选中记录信息
        records = get_all_records(self.current_user)
        record = None
        for r in records:
            if r['id'] == rid:
                record = r
                break
        if not record:
            return
        self._show_edit_dialog(record)

    def _show_edit_dialog(self, record):
        """弹出编辑记录对话框"""
        top = Toplevel(self.root)
        top.title('编辑记录')
        top.geometry('500x350')
        top.configure(bg=CARD)
        top.resizable(False, False)
        top.grab_set()
        top.transient(self.root)

        Label(top, text='编辑生产记录', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(pady=(12, 8))

        f = Frame(top, bg=CARD)
        f.pack(padx=24, fill=X)

        # 工人选择
        workers = get_workers()
        w_names = [w['name'] for w in workers]
        default_w = record.get('worker_name', '')
        w_idx = 0
        for i, w in enumerate(workers):
            if w['name'] == default_w:
                w_idx = i
                break

        Label(f, text='工人：', bg=CARD, font=('Microsoft YaHei', 10)).grid(row=0, column=0, sticky=W, pady=4)
        cb_w = ttk.Combobox(f, values=w_names, state='readonly', width=15, font=('Microsoft YaHei', 10))
        cb_w.grid(row=0, column=1, pady=4, sticky=W)
        if w_names:
            cb_w.current(w_idx)

        # 工序
        processes = get_processes()
        p_names = [f"{p['material']} - {p['process_name']}" for p in processes]
        default_p = f"{record.get('material', '')} - {record.get('process_name', '')}"
        p_idx = 0
        for i, p in enumerate(p_names):
            if p == default_p:
                p_idx = i
                break

        Label(f, text='工序：', bg=CARD, font=('Microsoft YaHei', 10)).grid(row=1, column=0, sticky=W, pady=4)
        cb_p = ttk.Combobox(f, values=p_names, state='readonly', width=25, font=('Microsoft YaHei', 10))
        cb_p.grid(row=1, column=1, pady=4, sticky=W)
        if p_names:
            cb_p.current(p_idx)

        # 件数
        Label(f, text='件数：', bg=CARD, font=('Microsoft YaHei', 10)).grid(row=2, column=0, sticky=W, pady=4)
        e_qty = Entry(f, width=10, font=('Microsoft YaHei', 11), relief='solid', bd=1, justify=CENTER)
        e_qty.grid(row=2, column=1, pady=4, sticky=W)
        e_qty.insert(0, str(int(record['quantity']) if record['quantity'] == int(record['quantity']) else record['quantity']))

        # 日期
        Label(f, text='日期：', bg=CARD, font=('Microsoft YaHei', 10)).grid(row=3, column=0, sticky=W, pady=4)
        e_date = Entry(f, width=14, font=('Microsoft YaHei', 11), relief='solid', bd=1, justify=CENTER)
        e_date.grid(row=3, column=1, pady=4, sticky=W)
        e_date.insert(0, record.get('record_date', ''))
        e_date.bind('<Button-1>', lambda e: self.show_calendar(e_date))

        def do_save():
            w_sel = cb_w.current()
            p_sel = cb_p.current()
            qty_s = e_qty.get().strip()
            d = e_date.get().strip()
            if w_sel < 0 or p_sel < 0:
                messagebox.showinfo('提示', '请选择工人和工序')
                return
            try:
                qty = float(qty_s)
            except ValueError:
                messagebox.showinfo('提示', '件数必须为数字')
                return
            wid = workers[w_sel]['id']
            pid = processes[p_sel]['id']
            price = processes[p_sel]['unit_price']
            update_record(record['id'], wid, pid, qty, price, d)
            messagebox.showinfo('成功', '记录已更新')
            top.destroy()
            self.refresh()

        btn_f = Frame(top, bg=CARD)
        btn_f.pack(pady=(12, 0))
        Button(btn_f, text='保存修改', bg=ACCENT, fg='white', font=('Microsoft YaHei', 10, 'bold'),
               relief='flat', padx=20, pady=3, cursor='hand2', command=do_save).pack(side=LEFT, padx=4)
        Button(btn_f, text='取消', bg='#95a5a6', fg='white', font=('Microsoft YaHei', 10, 'bold'),
               relief='flat', padx=20, pady=3, cursor='hand2', command=top.destroy).pack(side=LEFT, padx=4)
    
    def open_chart(self):
        stats = get_stats()
        gen_report(stats, '生产记录统计')

    def _export_table(self):
        """将当前表格数据导出到 Excel"""
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            messagebox.showinfo('提示', '请先安装 openpyxl:\npip install openpyxl')
            return
        records = get_all_records(self.current_user)
        if not records:
            messagebox.showinfo('提示', '没有可导出的数据')
            return
        from datetime import datetime
        fname = f'生产记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        path = os.path.join(_BASE, fname)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '生产记录'
        headers = ['ID', '物料', '工序', '工人', '组别', '件数', '单价', '工资', '日期']
        for ci, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.font = Font(bold=True, color='00ffffff')
            cell.fill = PatternFill('solid', fgColor='001a73e8')
            cell.alignment = Alignment(horizontal='center')
        for ri, r in enumerate(records, 2):
            ws.cell(row=ri, column=1, value=r['id'])
            ws.cell(row=ri, column=2, value=r.get('material', ''))
            ws.cell(row=ri, column=3, value=r.get('process_name', ''))
            ws.cell(row=ri, column=4, value=r.get('worker_name', ''))
            ws.cell(row=ri, column=5, value=r.get('group_name', ''))
            ws.cell(row=ri, column=6, value=r['quantity'])
            ws.cell(row=ri, column=7, value=r['unit_price'])
            ws.cell(row=ri, column=8, value=round(r['quantity'] * r['unit_price'], 2))
            ws.cell(row=ri, column=9, value=r['record_date'])
        wb.save(path)
        messagebox.showinfo('成功', f'已导出: {fname}')
    
    def monthly_summary(self):
        top = Toplevel(self.root); top.title('月度汇总'); top.geometry('700x500')
        top.configure(bg=CARD); top.grab_set()
        Label(top, text='选择月份', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(pady=(10,4))
        months = list_months()
        if not months:
            Label(top, text='暂无数据', bg=CARD, fg='#888').pack(); return
        cb = ttk.Combobox(top, values=months, state='readonly', width=12, font=('Microsoft YaHei',11))
        cb.pack(pady=4); cb.set(months[0] if months else '')
        
        def do():
            m = cb.get()
            if not m: return
            import calendar as cal_mod
            y, mo = int(m.split('-')[0]), int(m.split('-')[1])
            _, ld = cal_mod.monthrange(y, mo)
            stats = get_stats(start_date=m+'-01', end_date=f'{m}-{ld:02d}')
            gen_report(stats, f'{m} 月度汇总')
        
        Button(top, text='生成报告', command=do, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei',10,'bold'), relief='flat', padx=14, pady=4, cursor='hand2').pack(pady=6)
        
        tr = ttk.Treeview(top, columns=('name','group','qty','wage'), show='headings', height=10)
        for col, text, w in [('name','工人',100),('group','组别',100),('qty','件数',80),('wage','工资',100)]:
            tr.heading(col, text=text); tr.column(col, width=w)
        tr.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        def refresh():
            tr.delete(*tr.get_children())
            m = cb.get()
            if not m: return
            stats = get_stats(start_date=m+'-01', end_date=f'{m}-{ld:02d}')
            for r in stats.get('by_worker',[]):
                tr.insert('', END, values=(r['worker'],r['group_name'],r['q'],round(r['e'],2)))
        
        cb.bind('<<ComboboxSelected>>', lambda e: refresh())
        if months: refresh()
        
        def do_export():
            m = cb.get()
            if not m: return
            path = os.path.join(_BASE, f'月度汇总_{m}.xlsx')
            import calendar as cal_mod
            y, mo = int(m.split('-')[0]), int(m.split('-')[1])
            _, ld = cal_mod.monthrange(y, mo)
            stats = get_stats(start_date=m+'-01', end_date=f'{m}-{ld:02d}')
            if export_excel(stats, path, f'{m} 月度汇总'):
                messagebox.showinfo('成功', f'已导出: {path}')
        
        Button(top, text='导出 Excel', command=do_export, bg=GREEN, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(pady=(0,8))
    
    # ── Management dialogs ──
    def manage_materials(self):
        MaterialDialog(self.root)
    
    def manage_workers(self):
        WorkerDialog(self.root)
    
    def manage_processes(self):
        ProcessDialog(self.root)
    
    def manage_users(self):
        top = Toplevel(self.root); top.title('用户管理'); top.geometry('700x500')
        top.configure(bg=CARD); top.grab_set()
        Label(top, text='用户列表', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10,4))
        tr = ttk.Treeview(top, columns=('username','display','role','created'), show='headings', height=10)
        tr.heading('username', text='用户名'); tr.heading('display', text='显示名')
        tr.heading('role', text='角色'); tr.heading('created', text='创建时间')
        tr.column('username', width=120); tr.column('display', width=120)
        tr.column('role', width=100); tr.column('created', width=150)
        def ref():
            tr.delete(*tr.get_children())
            for u in get_users():
                role_text = {'admin':'管理员','leader':'班组长','worker':'普通用户'}.get(u['role'], u['role'])
                tr.insert('', END, values=(u['username'], u['display_name'], role_text, u.get('created_at','')))
        ref(); tr.pack(fill=BOTH, expand=True, padx=16, pady=(0,4))
        f = Frame(top, bg=CARD); f.pack(fill=X, padx=16, pady=(0,6))
        e_un = Entry(f, width=12, font=('Microsoft YaHei',11), relief='solid', bd=1); e_un.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_un, '用户名')
        e_dn = Entry(f, width=10, font=('Microsoft YaHei',11), relief='solid', bd=1); e_dn.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_dn, '显示名')
        e_pw = Entry(f, width=10, font=('Microsoft YaHei',11), relief='solid', bd=1, show='*')
        e_pw.pack(side=LEFT, padx=(0,4)); _set_placeholder(e_pw, '密码')
        role_cb = ttk.Combobox(f, values=['管理员','班组长','普通用户'], state='readonly', width=8)
        role_cb.pack(side=LEFT, padx=(0,4)); role_cb.set('普通用户')
        def do_add():
            un = e_un.get().strip(); dn = e_dn.get().strip(); pw = e_pw.get().strip()
            if un == getattr(e_un,'_ph_text',None): un = ''
            if dn == getattr(e_dn,'_ph_text',None): dn = ''
            if pw == getattr(e_pw,'_ph_text',None): pw = ''
            if not un or not pw: messagebox.showinfo('提示','用户名和密码不能为空'); return
            role_map = {'管理员':'admin','班组长':'leader','普通用户':'worker'}
            role = role_map.get(role_cb.get(), 'worker')
            if add_user(un, pw, dn, role):
                ref(); e_un.delete(0,END); e_dn.delete(0,END); e_pw.delete(0,END)
            else: messagebox.showinfo('提示','用户名已存在')
        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei',9,'bold'),
               relief='flat', padx=8, cursor='hand2', command=do_add).pack(side=LEFT, padx=(4,0))
        def do_del():
            sel = tr.selection()
            if not sel: return
            v = tr.item(sel[0],'values')
            if v[0] == 'admin': messagebox.showinfo('提示','不能删除 admin 账户'); return
            if messagebox.askyesno('确认', f'删除用户 "{v[0]}"？'):
                delete_user(v[0]); ref()
        Button(f, text='删除', bg=RED, fg='white', font=('Microsoft YaHei',9,'bold'),
               relief='flat', padx=8, cursor='hand2', command=do_del).pack(side=LEFT, padx=(4,0))
    
    def manage_permissions(self):
        top = Toplevel(self.root); top.title('权限管理'); top.geometry('1000x500')
        top.configure(bg=CARD); top.grab_set()
        Label(top, text='权限管理', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10,4))
        Label(top, text='点击复选框切换权限', font=('Microsoft YaHei',9), bg=CARD, fg='#888').pack(anchor=W, padx=16)
        
        # Scrollable frame
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
        
        users = get_users()
        perm_labels = [('record_add','添加记录'),('record_delete','删除记录'),('record_edit','编辑记录'),
                      ('material_manage','管理物料'),('worker_manage','管理工人'),('process_manage','管理工序'),
                      ('assignment_manage','工序分配'),('chart_view','查看图表'),('summary_view','查看汇总'),
                      ('export_excel','导出Excel'),('user_manage','用户管理')]
        perms = [p[0] for p in perm_labels]
        
        # Header
        Label(frame, text='用户', bg=CARD, fg=DARK, font=('Microsoft YaHei',9,'bold'),
              width=10, anchor='w').grid(row=0, column=0, padx=4, pady=2, sticky='w')
        for ci, (pk, pl) in enumerate(perm_labels, 1):
            Label(frame, text=pl, bg=CARD, fg='#555', font=('Microsoft YaHei',8),
                  width=7, anchor='w').grid(row=0, column=ci, padx=2, pady=2)
        
        # Permission checkboxes
        self._perm_vars = {}
        for ri, u in enumerate(users, 1):
            un = u['username']
            Label(frame, text=un, bg=CARD, fg=DARK, font=('Microsoft YaHei',9),
                  width=10, anchor='w').grid(row=ri, column=0, padx=4, pady=1, sticky='w')
            perms_dict = get_user_perms(un)
            for ci, pk in enumerate(perms, 1):
                var = IntVar(value=perms_dict.get(pk, 0))
                self._perm_vars[(un, pk)] = var
                def make_cmd(u_name, p_key):
                    return lambda: set_user_perm(u_name, p_key, self._perm_vars[(u_name, p_key)].get())
                cb = Checkbutton(frame, variable=var, bg=CARD, command=make_cmd(un, pk))
                cb.grid(row=ri, column=ci)
    
    def show_calendar(self, entry):
        """弹出日历选择器，选中日期后填入 entry"""
        top = Toplevel(self.root); top.title('选择日期')
        top.geometry('300x260'); top.resizable(False, False)
        top.configure(bg=CARD); top.grab_set(); top.transient(self.root)
        xp = self.root.winfo_x()+self.root.winfo_width()//2-150
        yp = self.root.winfo_y()+self.root.winfo_height()//2-130
        top.geometry(f'+{xp}+{yp}')
        
        now = date.today()
        state = {'y': now.year, 'm': now.month}
        
        head = Frame(top, bg=CARD); head.pack(fill=X, padx=8, pady=(8,4))
        btn_prev = Button(head, text='‹', bg='#eee', relief='flat', padx=4, cursor='hand2',
                         font=('Microsoft YaHei',10,'bold'))
        btn_prev.pack(side=LEFT)
        title_lbl = Label(head, bg=CARD, fg=DARK, font=('Microsoft YaHei',11,'bold'))
        title_lbl.pack(side=LEFT, expand=True)
        btn_next = Button(head, text='›', bg='#eee', relief='flat', padx=4, cursor='hand2',
                         font=('Microsoft YaHei',10,'bold'))
        btn_next.pack(side=RIGHT)
        
        grid = Frame(top, bg=CARD); grid.pack(padx=8, fill=BOTH, expand=True)
        for ci, d in enumerate(['一','二','三','四','五','六','日']):
            Label(grid, text=d, bg=CARD, fg='#888', font=('Microsoft YaHei',8), width=4).grid(row=0, column=ci, padx=1, pady=1)
        
        def rebuild():
            nonlocal state
            for w in grid.winfo_children():
                if int(w.grid_info()['row']) > 0:
                    w.destroy()
            title_lbl.config(text=f'{state["y"]}年{state["m"]}月')
            import calendar as cal_mod
            cal = cal_mod.monthcalendar(state['y'], state['m'])
            today = date.today()
            for ri, week in enumerate(cal, 1):
                for ci, d in enumerate(week):
                    if d == 0: continue
                    is_today = (state['y']==today.year and state['m']==today.month and d==today.day)
                    bg = '#1a73e8' if is_today else 'white'; fg = 'white' if is_today else DARK
                    btn = Button(grid, text=str(d), bg=bg, fg=fg, font=('Microsoft YaHei',9),
                                relief='flat', width=4, cursor='hand2',
                                command=lambda dd=d: [entry.delete(0,END), entry.insert(0,f'{state["y"]}-{state["m"]:02d}-{dd:02d}'), top.destroy()])
                    btn.grid(row=ri, column=ci, padx=1, pady=1)
        
        def prev():
            nonlocal state
            if state['m'] == 1: state['y'] -= 1; state['m'] = 12
            else: state['m'] -= 1
            rebuild()
        
        def next_m():
            nonlocal state
            if state['m'] == 12: state['y'] += 1; state['m'] = 1
            else: state['m'] += 1
            rebuild()
        
        btn_prev.config(command=prev)
        btn_next.config(command=next_m)
        rebuild()
    
    def summary_page(self):
        top = Toplevel(self.root); top.title('汇总查询'); top.geometry('800x550')
        top.configure(bg=CARD); top.grab_set()
        Label(top, text='汇总查询', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(anchor=W, padx=16, pady=(10,4))
        
        # Filters
        ff = Frame(top, bg=CARD); ff.pack(fill=X, padx=16)
        Label(ff, text='起始日期:', bg=CARD, fg='#555', font=('Microsoft YaHei',9)).pack(side=LEFT)
        e_start = Entry(ff, width=12, font=('Microsoft YaHei',10), relief='solid', bd=1)
        e_start.bind('<Button-1>', lambda e: self.show_calendar(e_start))
        e_start.pack(side=LEFT, padx=(2,8))
        Label(ff, text='结束日期:', bg=CARD, fg='#555', font=('Microsoft YaHei',9)).pack(side=LEFT)
        e_end = Entry(ff, width=12, font=('Microsoft YaHei',10), relief='solid', bd=1)
        e_end.bind('<Button-1>', lambda e: self.show_calendar(e_end))
        e_end.pack(side=LEFT, padx=(2,8))
        
        workers = get_workers()
        cb_worker = ttk.Combobox(ff, values=['全部']+[w['name'] for w in workers], state='readonly', width=10)
        cb_worker.pack(side=LEFT, padx=(4,4)); cb_worker.set('全部')
        
        def do_query():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel-1]['id']
            stats = get_stats(start_date=sd, end_date=ed, worker_filter=wf)
            gen_report(stats, '汇总查询结果')
        
        Button(ff, text='查询', command=do_query, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT, padx=(8,0))
        
        # Stats table
        tr = ttk.Treeview(top, columns=('worker','group','qty','wage'), show='headings', height=12)
        tr.heading('worker', text='工人'); tr.heading('group', text='组别')
        tr.heading('qty', text='件数'); tr.heading('wage', text='工资')
        tr.column('worker', width=120); tr.column('group', width=120)
        tr.column('qty', width=100); tr.column('wage', width=120)
        tr.pack(fill=BOTH, expand=True, padx=16, pady=(8,4))
        
        def do_query_table():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel-1]['id']
            stats = get_stats(start_date=sd, end_date=ed, worker_filter=wf)
            tr.delete(*tr.get_children())
            for r in stats.get('by_worker',[]):
                tr.insert('', END, values=(r['worker'], r['group_name'], r['q'], round(r['e'],2)))
        
        def do_export():
            sd = e_start.get().strip() or None
            ed = e_end.get().strip() or None
            wf = None
            sel = cb_worker.current()
            if sel > 0 and sel <= len(workers):
                wf = workers[sel-1]['id']
            stats = get_stats(start_date=sd, end_date=ed, worker_filter=wf)
            path = os.path.join(_BASE, '汇总查询.xlsx')
            title = '汇总查询'
            if sd or ed: title += f' ({sd or ""}~{ed or ""})'
            if export_excel(stats, path, title):
                messagebox.showinfo('成功', f'已导出: {path}')
        
        bf = Frame(top, bg=CARD); bf.pack(fill=X, padx=16, pady=(0,8))
        Button(bf, text='查询表格', command=do_query_table, bg=PRIMARY, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT, padx=(0,6))
        Button(bf, text='导出 Excel', command=do_export, bg=GREEN, fg='white',
               font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, cursor='hand2').pack(side=LEFT)

if __name__ == '__main__':
    init_db()
    app = App()
    app.root.mainloop()
