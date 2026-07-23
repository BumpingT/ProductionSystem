"""
应用配置 — 集中管理所有常量
"""
import os, sys

def _rp(rel):
    try: base = sys._MEIPASS
    except: base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

_IS_FROZEN = getattr(sys, 'frozen', False)
_BASE = os.path.dirname(sys.executable) if _IS_FROZEN else os.path.dirname(os.path.abspath(__file__))

# ── 路径 ──
DB_PATH = os.path.join(_BASE, 'data.db')
ECHARTS_PATH = _rp('echarts.min.js')
LOGIN_CRED_PATH = os.path.join(_BASE, '.login_cred')

# ── 颜色主题 ──
BG = '#f0f2f5'
CARD = '#ffffff'
PRIMARY = '#1a73e8'
ACCENT = '#e67e22'
GREEN = '#27ae60'
RED = '#e74c3c'
DARK = '#2c3e50'

# ── 权限 ──
ALL_PERMS = ['record_add','record_delete','record_edit','material_manage',
             'worker_manage','process_manage','assignment_manage','chart_view',
             'summary_view','monthly_view','export_excel','user_manage']

ROLE_ADMIN = 'admin'
ROLE_LEADER = 'leader'
ROLE_MANAGER = 'manager'
ROLE_WORKER = 'worker'

# 角色中文名称映射
ROLE_NAMES = {
    'admin': '管理员',
    'manager': '生产部部长',
    'leader': '组长',
    'worker': '生产工人',
}
ROLE_NAMES_REV = {v: k for k, v in ROLE_NAMES.items()}

# ── 货币符号 ──
YEN = chr(0xa5)
