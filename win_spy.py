"""
Windows 窗口实时侦查 + 修改工具
功能: 查看exe窗口控件、实时监控变化、修改窗口属性

用法:
  python win_spy.py          # 普通模式
  python win_spy.py --monitor # 启动后自动进入监控模式
"""
import win32gui, win32con, win32api, win32process
import sys, re, time, struct, threading
import tkinter as tk
from tkinter import ttk, messagebox

# ── 工具函数 ──

def get_window_info(hwnd):
    try:
        text = win32gui.GetWindowText(hwnd) or ''
        cls = win32gui.GetClassName(hwnd) or ''
        rect = win32gui.GetWindowRect(hwnd)
        x, y, w, h = rect
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        visible = bool(style & win32con.WS_VISIBLE)
        enabled = bool(style & win32con.WS_DISABLED) == False
        parent = win32gui.GetParent(hwnd)
        # 获取进程ID
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return {
            'hwnd': hwnd,
            'text': text[:100],
            'class': cls[:50],
            'x': x, 'y': y, 'w': w-x, 'h': h-y,
            'visible': visible,
            'enabled': enabled,
            'parent': parent,
            'pid': pid,
            'style': style,
            'exstyle': exstyle,
        }
    except:
        return None

def enum_children(parent_hwnd):
    """返回子窗口列表（递归）"""
    result = []
    def cb(hwnd, _):
        info = get_window_info(hwnd)
        if info:
            result.append(info)
        return True
    win32gui.EnumChildWindows(parent_hwnd, cb, None)
    return result

def get_all_top_windows():
    """所有可见顶级窗口"""
    result = []
    def cb(hwnd, _):
        info = get_window_info(hwnd)
        if info:
            result.append(info)
        return True
    win32gui.EnumWindows(cb, None)
    return result

def flash_window(hwnd, count=3):
    """闪烁窗口"""
    for _ in range(count):
        win32gui.FlashWindow(hwnd, True)
        time.sleep(0.15)
        win32gui.FlashWindow(hwnd, False)
        time.sleep(0.15)

def set_window_text(hwnd, text):
    """修改窗口标题/控件文本"""
    try:
        win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, 0, text)
        return True
    except:
        return False

def set_window_visible(hwnd, show):
    """显示/隐藏窗口"""
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW if show else win32con.SW_HIDE)
        return True
    except:
        return False

def move_window(hwnd, x, y, w, h):
    """移动/调整窗口大小"""
    try:
        win32gui.SetWindowPos(hwnd, 0, x, y, w, h, 
                              win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW)
        return True
    except:
        return False

def highlight_window(hwnd, color=0x0000FF):
    """在窗口周围画边框"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        x, y, w, h = rect
        dc = win32gui.GetDC(0)
        pen = win32gui.CreatePen(win32con.PS_SOLID, 3, color)
        old_pen = win32gui.SelectObject(dc, pen)
        old_brush = win32gui.SelectObject(dc, win32gui.GetStockObject(win32con.NULL_BRUSH))
        win32gui.Rectangle(dc, x, y, w, h)
        win32gui.SelectObject(dc, old_pen)
        win32gui.SelectObject(dc, old_brush)
        win32gui.ReleaseDC(0, dc)
        return True
    except:
        return False

def get_process_name(pid):
    """获取进程名"""
    try:
        handle = win32api.OpenProcess(0x0400 | 0x0010, False, pid)
        if handle:
            exe = win32process.GetModuleFileNameEx(handle, 0)
            win32api.CloseHandle(handle)
            return exe.split('\\')[-1] if exe else f'PID:{pid}'
    except:
        pass
    return f'PID:{pid}'

# ── 主应用 ──

class WinSpyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('WinSpy - 窗口实时侦查工具')
        self.root.geometry('1100x700')
        self.root.configure(bg='#f0f2f5')
        
        self.monitoring = False
        self.monitor_timer = None
        self.selected_hwnd = None
        self.all_windows = []
        self.previous_state = {}  # 用于检测变化
        
        self.build_ui()
        self.refresh()
    
    def build_ui(self):
        # ── 顶部工具栏 ──
        toolbar = tk.Frame(self.root, bg='#2c3e50', height=36)
        toolbar.pack(fill=tk.X)
        
        tk.Label(toolbar, text='🔍 WinSpy', bg='#2c3e50', fg='white',
                font=('Microsoft YaHei', 11, 'bold')).pack(side=tk.LEFT, padx=10)
        
        self.monitor_btn = tk.Button(toolbar, text='▶ 开始监控', 
            command=self.toggle_monitor, bg='#27ae60', fg='white',
            relief='flat', padx=12, cursor='hand2', font=('Microsoft YaHei', 9))
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text='🔄 刷新', command=self.refresh,
            bg='#3498db', fg='white', relief='flat', padx=12, cursor='hand2',
            font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text='🔦 高亮', command=self.do_highlight,
            bg='#e67e22', fg='white', relief='flat', padx=12, cursor='hand2',
            font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(toolbar, text='❌ 关闭', command=self.root.quit,
            bg='#e74c3c', fg='white', relief='flat', padx=12, cursor='hand2',
            font=('Microsoft YaHei', 9)).pack(side=tk.RIGHT, padx=5)
        
        # 搜索框
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self.filter_list())
        tk.Entry(toolbar, textvariable=self.search_var, width=20, relief='flat',
                font=('Microsoft YaHei', 9), bg='#ecf0f1').pack(side=tk.RIGHT, padx=5)
        tk.Label(toolbar, text='搜索:', bg='#2c3e50', fg='#bbb',
                font=('Microsoft YaHei', 9)).pack(side=tk.RIGHT)
        
        # ── 状态栏 ──
        self.status_var = tk.StringVar(value='就绪 | F5刷新 | 点击窗口查看属性 | 监控模式自动检测变化')
        status = tk.Label(self.root, textvariable=self.status_var,
                         bg='#34495e', fg='#ecf0f1', font=('Microsoft YaHei', 8),
                         anchor='w', padx=10)
        status.pack(fill=tk.X)
        
        # ── 主分割面板 ──
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg='#ccc')
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # ======================= 左侧：窗口树 =======================
        left = tk.Frame(paned, bg='white')
        paned.add(left, width=400)
        
        tk.Label(left, text='📋 窗口列表（按进程分组）', font=('Microsoft YaHei', 10, 'bold'),
                bg='#f8f9fa', fg='#333', anchor='w', padx=8).pack(fill=tk.X)
        
        tree_frame = tk.Frame(left)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, columns=('hwnd', 'cls', 'rect'), show='tree headings')
        self.tree.heading('#0', text='标题 / 文本')
        self.tree.heading('hwnd', text='句柄')
        self.tree.heading('cls', text='类名')
        self.tree.heading('rect', text='位置')
        self.tree.column('#0', width=200, minwidth=120)
        self.tree.column('hwnd', width=80)
        self.tree.column('cls', width=100)
        self.tree.column('rect', width=120)
        
        tsb = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # ======================= 右侧：属性 + 操作 =======================
        right = tk.Frame(paned, bg='white')
        paned.add(right, width=600)
        
        # 笔记本标签页
        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # ── Tab 1: 属性 ──
        prop_tab = tk.Frame(nb, bg='#f8f9fa')
        nb.add(prop_tab, text='📝 属性')
        
        # 属性网格
        prop_canvas = tk.Canvas(prop_tab, bg='#f8f9fa', highlightthickness=0)
        prop_scroll = tk.Scrollbar(prop_tab, orient=tk.VERTICAL, command=prop_canvas.yview)
        prop_inner = tk.Frame(prop_canvas, bg='#f8f9fa')
        
        prop_canvas.configure(yscrollcommand=prop_scroll.set)
        prop_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prop_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        prop_canvas.create_window((0, 0), window=prop_inner, anchor='nw')
        
        prop_inner.bind('<Configure>', lambda e: prop_canvas.configure(scrollregion=prop_canvas.bbox('all')))
        
        self.props = {}
        fields = [
            ('hwnd', '句柄 (HWND)', ''),
            ('text', '标题 (Text)', ''),
            ('class', '类名 (Class)', ''),
            ('x', 'X 坐标', 'px'),
            ('y', 'Y 坐标', 'px'),
            ('w', '宽度', 'px'),
            ('h', '高度', 'px'),
            ('visible', '可见', ''),
            ('enabled', '启用', ''),
            ('parent', '父窗口句柄', ''),
            ('pid', '进程 ID', ''),
            ('style', '样式', 'hex'),
        ]
        for key, label, unit in fields:
            row = tk.Frame(prop_inner, bg='#f8f9fa')
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=label, width=16, anchor='e', bg='#f8f9fa',
                    fg='#555', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
            val = tk.Label(row, text='-', anchor='w', bg='white', fg='#333',
                          font=('Consolas', 9), relief='solid', bd=1, padx=4)
            val.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.props[key] = val
        
        # 带修改框的属性
        tk.Frame(prop_inner, bg='#f8f9fa', height=10).pack()
        tk.Label(prop_inner, text='✏️ 修改窗口属性', font=('Microsoft YaHei', 9, 'bold'),
                bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=10)
        
        edit_frame = tk.Frame(prop_inner, bg='#f8f9fa')
        edit_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 修改标题
        row1 = tk.Frame(edit_frame, bg='#f8f9fa')
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text='新标题:', width=12, anchor='e', bg='#f8f9fa',
                fg='#555', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        self.edit_title = tk.Entry(row1, relief='solid', bd=1, font=('Microsoft YaHei', 9))
        self.edit_title.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(row1, text='应用', command=self.apply_title, bg='#3498db', fg='white',
                 relief='flat', padx=8, cursor='hand2', font=('Microsoft YaHei', 8)).pack(side=tk.RIGHT)
        
        # 移动窗口
        row2 = tk.Frame(edit_frame, bg='#f8f9fa')
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text='移动到(X,Y):', width=12, anchor='e', bg='#f8f9fa',
                fg='#555', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        self.edit_x = tk.Entry(row2, width=6, relief='solid', bd=1)
        self.edit_x.pack(side=tk.LEFT, padx=(0, 2))
        tk.Label(row2, text='x', bg='#f8f9fa').pack(side=tk.LEFT)
        self.edit_y = tk.Entry(row2, width=6, relief='solid', bd=1)
        self.edit_y.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text='宽:', bg='#f8f9fa').pack(side=tk.LEFT, padx=(10, 2))
        self.edit_w = tk.Entry(row2, width=6, relief='solid', bd=1)
        self.edit_w.pack(side=tk.LEFT, padx=2)
        tk.Label(row2, text='高:', bg='#f8f9fa').pack(side=tk.LEFT, padx=(5, 2))
        self.edit_h = tk.Entry(row2, width=6, relief='solid', bd=1)
        self.edit_h.pack(side=tk.LEFT, padx=2)
        tk.Button(row2, text='移动', command=self.apply_move, bg='#e67e22', fg='white',
                 relief='flat', padx=8, cursor='hand2', font=('Microsoft YaHei', 8)).pack(side=tk.LEFT, padx=5)
        
        # 显示/隐藏/闪烁
        row3 = tk.Frame(edit_frame, bg='#f8f9fa')
        row3.pack(fill=tk.X, pady=5)
        tk.Button(row3, text='👁 显示', command=lambda: self.set_vis(True),
                 bg='#27ae60', fg='white', relief='flat', padx=8, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(row3, text='🙈 隐藏', command=lambda: self.set_vis(False),
                 bg='#e74c3c', fg='white', relief='flat', padx=8, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(row3, text='💡 闪烁', command=self.do_flash,
                 bg='#f39c12', fg='white', relief='flat', padx=8, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(row3, text='🔦 高亮', command=self.do_highlight,
                 bg='#9b59b6', fg='white', relief='flat', padx=8, cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        # ── Tab 2: 子控件 ──
        child_tab = tk.Frame(nb, bg='white')
        nb.add(child_tab, text='🔧 子控件')
        
        self.child_tree = ttk.Treeview(child_tab,
            columns=('hwnd', 'class', 'x', 'y', 'w', 'h', 'visible', 'text'),
            show='headings')
        self.child_tree.heading('hwnd', text='句柄')
        self.child_tree.heading('class', text='类名')
        self.child_tree.heading('x', text='X')
        self.child_tree.heading('y', text='Y')
        self.child_tree.heading('w', text='宽')
        self.child_tree.heading('h', text='高')
        self.child_tree.heading('visible', text='可见')
        self.child_tree.heading('text', text='文本')
        for col, w in [('hwnd', 80), ('class', 100), ('x', 50), ('y', 50),
                       ('w', 50), ('h', 50), ('visible', 45), ('text', 150)]:
            self.child_tree.column(col, width=w)
        
        csvb = tk.Scrollbar(child_tab, orient=tk.VERTICAL, command=self.child_tree.yview)
        self.child_tree.configure(yscrollcommand=csvb.set)
        self.child_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        csvb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.child_tree.bind('<ButtonRelease-1>', self.on_child_click)
        
        # ── Tab 3: 实时监控 ──
        mon_tab = tk.Frame(nb, bg='#1a1a2e')
        nb.add(mon_tab, text='📊 实时监控')
        
        self.monitor_text = tk.Text(mon_tab, bg='#1a1a2e', fg='#00ff00',
            font=('Consolas', 9), relief='flat', state='disabled', wrap=tk.WORD)
        self.monitor_text.pack(fill=tk.BOTH, expand=True)
        
        mon_ctrl = tk.Frame(mon_tab, bg='#16213e')
        mon_ctrl.pack(fill=tk.X)
        tk.Label(mon_ctrl, text='监控间隔(秒):', bg='#16213e', fg='#aaa',
                font=('Microsoft YaHei', 8)).pack(side=tk.LEFT, padx=5)
        self.monitor_interval = tk.StringVar(value='1')
        tk.Entry(mon_ctrl, textvariable=self.monitor_interval, width=4,
                bg='#0f3460', fg='white', relief='flat', justify='center').pack(side=tk.LEFT)
        tk.Button(mon_ctrl, text='清空', command=lambda: self.monitor_text.configure(state='normal') or 
                 self.monitor_text.delete('1.0', tk.END) or self.monitor_text.configure(state='disabled'),
                 bg='#e74c3c', fg='white', relief='flat', padx=6, cursor='hand2').pack(side=tk.RIGHT, padx=5)
        
        # 绑定键盘
        self.root.bind('<F5>', lambda e: self.refresh())
        
        # 监控标记
        self.monitoring = False
        self.monitor_job = None
    
    def log_monitor(self, msg):
        """向监控面板追加日志"""
        self.monitor_text.configure(state='normal')
        ts = time.strftime('%H:%M:%S')
        self.monitor_text.insert(tk.END, f'[{ts}] {msg}\n')
        self.monitor_text.see(tk.END)
        self.monitor_text.configure(state='disabled')
    
    def toggle_monitor(self):
        """切换监控模式"""
        self.monitoring = not self.monitoring
        if self.monitoring:
            self.monitor_btn.configure(text='⏹ 停止监控', bg='#e74c3c')
            self.previous_state = {}
            self.log_monitor('🚀 监控已启动 (间隔: %s秒)' % self.monitor_interval.get())
            self.monitor_loop()
        else:
            self.monitor_btn.configure(text='▶ 开始监控', bg='#27ae60')
            if self.monitor_job:
                self.root.after_cancel(self.monitor_job)
                self.monitor_job = None
            self.log_monitor('⏹ 监控已停止')
    
    def monitor_loop(self):
        """监控循环 - 检测窗口变化"""
        if not self.monitoring:
            return
        try:
            interval = float(self.monitor_interval.get())
        except:
            interval = 1.0
        
        # 获取当前所有窗口
        current = get_all_top_windows()
        current_dict = {w['hwnd']: w for w in current}
        
        # 检测变化
        # 1. 新窗口出现
        for w in current:
            hwnd = w['hwnd']
            if hwnd not in self.previous_state:
                text = w['text']
                cls = w['class']
                if text or cls != 'Tooltip':
                    self.log_monitor(f'🟢 新窗口: 0x{hwnd:08X} [{cls}] {text[:50]}')
        
        # 2. 窗口消失
        for hwnd in list(self.previous_state.keys()):
            if hwnd not in current_dict:
                old = self.previous_state[hwnd]
                self.log_monitor(f'🔴 窗口关闭: 0x{hwnd:08X} [{old["class"]}] {old["text"][:50]}')
        
        # 3. 标题变化
        for w in current:
            hwnd = w['hwnd']
            if hwnd in self.previous_state:
                old = self.previous_state[hwnd]
                if w['text'] != old['text']:
                    self.log_monitor(f'📝 标题变化: 0x{hwnd:08X} "{old["text"][:30]}" → "{w["text"][:30]}"')
                if (w['x'], w['y'], w['w'], w['h']) != (old['x'], old['y'], old['w'], old['h']):
                    self.log_monitor(f'📐 位置变化: 0x{hwnd:08X} ({old["x"]},{old["y"]})→({w["x"]},{w["y"]})')
                if w['visible'] != old['visible']:
                    self.log_monitor(f'{"👁" if w["visible"] else "🙈"} 可见变化: 0x{hwnd:08X} {w["text"][:30]}')
        
        # 保存当前状态
        self.previous_state = current_dict
        
        # 更新状态栏
        self.status_var.set(f'监控中 ... {len(current)} 个窗口 | 间隔: {interval}s | F5刷新')
        
        self.monitor_job = self.root.after(int(interval * 1000), self.monitor_loop)
    
    def refresh(self):
        """刷新窗口列表"""
        self.tree.delete(*self.tree.get_children())
        self.all_windows = get_all_top_windows()
        self.filter_list()
        self.status_var.set(f'已刷新: {len(self.all_windows)} 个窗口')
    
    def filter_list(self):
        """按搜索条件过滤"""
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        # 按进程分组
        by_pid = {}
        for win in self.all_windows:
            pid = win.get('pid', 0)
            if pid not in by_pid:
                pname = get_process_name(pid)
                by_pid[pid] = {'name': pname, 'children': []}
            by_pid[pid]['children'].append(win)
        
        for pid, group in sorted(by_pid.items(), key=lambda x: x[1]['name']):
            # 过滤：如果组内没有匹配的窗口，跳过整组
            matched = [w for w in group['children'] 
                      if not query or query in w['text'].lower() or query in w['class'].lower()]
            if query and not matched:
                continue
            
            # 如果没有搜索词，显示所有；否则只显示匹配的
            display_list = matched if query else group['children']
            if not display_list:
                continue
            
            pname = group['name']
            proc_item = self.tree.insert('', tk.END, text=f'📂 {pname} ({len(display_list)})',
                                        open=True, values=('', '', ''))
            
            for win in display_list:
                rect = f'({win["x"]},{win["y"]})-({win["w"]}x{win["h"]})'
                icon = '👁' if win['visible'] else '🙈'
                self.tree.insert(proc_item, tk.END,
                    text=f'{icon} {win["text"][:50]}',
                    values=(f'0x{win["hwnd"]:08X}', win['class'][:30], rect))
    
    def find_win_by_tree_iid(self, iid):
        """从 tree iid 查找窗口信息"""
        parent = self.tree.parent(iid)
        if not parent:
            return None
        # 获取该行的值
        vals = self.tree.item(iid, 'values')
        if not vals or not vals[0]:
            return None
        hwnd_str = vals[0]
        if hwnd_str.startswith('0x'):
            hwnd = int(hwnd_str, 16)
            for w in self.all_windows:
                if w['hwnd'] == hwnd:
                    return w
        return None
    
    def on_select(self, event):
        """选中窗口时更新属性"""
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        win = self.find_win_by_tree_iid(iid)
        if not win:
            return
        
        self.selected_hwnd = win['hwnd']
        
        # 更新属性
        for key in self.props:
            val = win.get(key, '-')
            if key == 'visible':
                val = '✓ 可见' if val else '✗ 隐藏'
            elif key == 'enabled':
                val = '✓ 启用' if val else '✗ 禁用'
            elif key == 'hwnd':
                val = f'0x{val:08X}'
            elif key == 'parent':
                val = f'0x{val:08X}' if val else '无'
            elif key == 'pid':
                val = f'{val} ({get_process_name(val)})'
            elif key == 'style':
                val = f'0x{val:08X}'
            self.props[key].config(text=str(val))
        
        # 填充编辑框
        self.edit_title.delete(0, tk.END)
        self.edit_title.insert(0, win['text'])
        self.edit_x.delete(0, tk.END)
        self.edit_x.insert(0, str(win['x']))
        self.edit_y.delete(0, tk.END)
        self.edit_y.insert(0, str(win['y']))
        self.edit_w.delete(0, tk.END)
        self.edit_w.insert(0, str(win['w']))
        self.edit_h.delete(0, tk.END)
        self.edit_h.insert(0, str(win['h']))
        
        # 更新子控件
        self.refresh_children(win['hwnd'])
        
        self.status_var.set(f'已选择: 0x{win["hwnd"]:08X} {win["class"]} "{win["text"][:40]}"')
    
    def on_double_click(self, event):
        """双击高亮"""
        self.do_highlight()
    
    def on_child_click(self, event):
        """点击子控件后高亮"""
        sel = self.child_tree.selection()
        if not sel:
            return
        vals = self.child_tree.item(sel[0], 'values')
        if vals and vals[0].startswith('0x'):
            hwnd = int(vals[0], 16)
            highlight_window(hwnd)
            self.status_var.set(f'高亮子控件: 0x{hwnd:08X}')
    
    def refresh_children(self, hwnd):
        """刷新子控件列表"""
        self.child_tree.delete(*self.child_tree.get_children())
        children = enum_children(hwnd)
        for child in children:
            self.child_tree.insert('', tk.END,
                values=(f'0x{child["hwnd"]:08X}', child['class'],
                       child['x'], child['y'], child['w'], child['h'],
                       '✓' if child['visible'] else '✗', child['text'][:40]))
    
    def do_highlight(self):
        """高亮选中的窗口"""
        if self.selected_hwnd:
            highlight_window(self.selected_hwnd)
            self.status_var.set(f'🔦 已高亮: 0x{self.selected_hwnd:08X}')
    
    def do_flash(self):
        """闪烁选中的窗口"""
        if self.selected_hwnd:
            threading.Thread(target=flash_window, args=(self.selected_hwnd, 5), daemon=True).start()
            self.status_var.set(f'💡 闪烁: 0x{self.selected_hwnd:08X}')
    
    def set_vis(self, show):
        """显示/隐藏窗口"""
        if self.selected_hwnd:
            if set_window_visible(self.selected_hwnd, show):
                self.status_var.set(f'{"显示" if show else "隐藏"} 窗口: 0x{self.selected_hwnd:08X}')
                self.refresh()
    
    def apply_title(self):
        """修改窗口标题"""
        if self.selected_hwnd:
            text = self.edit_title.get()
            if set_window_text(self.selected_hwnd, text):
                self.status_var.set(f'✅ 标题已修改: "{text}"')
                self.refresh()
    
    def apply_move(self):
        """移动窗口"""
        if self.selected_hwnd:
            try:
                x = int(self.edit_x.get())
                y = int(self.edit_y.get())
                w = int(self.edit_w.get())
                h = int(self.edit_h.get())
                if move_window(self.selected_hwnd, x, y, w, h):
                    self.status_var.set(f'✅ 窗口已移动到 ({x},{y}) 大小 ({w}x{h})')
                    self.refresh()
            except ValueError:
                messagebox.showwarning('输入错误', '请输入有效的数字')
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = WinSpyApp()
    app.run()
