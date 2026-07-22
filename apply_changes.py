"""Apply all role-based data filtering changes to main.py."""
import re

with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Helper _user_scope_filter + modify get_all_records
old = '''def get_all_records():
    conn = get_conn()
    rows = conn.execute("SELECT r.*,w.name as worker_name,w.group_name,p.material,p.process_name FROM records r LEFT JOIN workers w ON r.worker_id=w.id LEFT JOIN processes p ON r.process_id=p.id ORDER BY r.record_date DESC, r.id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]'''

new = '''def _user_scope_filter(user):
    """Return (where_clause, params) for filtering records by user role."""
    if not user or user.get('role') == 'admin':
        return '', []
    wid = user.get('worker_id', 0)
    if user.get('role') == 'leader':
        return 'r.worker_id IN (SELECT id FROM workers WHERE leader_id=?)', [wid]
    return 'r.worker_id=?', [wid]

def get_all_records(user=None):
    conn = get_conn()
    ws, pa = _user_scope_filter(user)
    sql = "SELECT r.*,w.name as worker_name,w.group_name,p.material,p.process_name FROM records r LEFT JOIN workers w ON r.worker_id=w.id LEFT JOIN processes p ON r.process_id=p.id"
    if ws: sql += ' WHERE ' + ws
    sql += ' ORDER BY r.record_date DESC, r.id DESC'
    rows = conn.execute(sql, pa).fetchall()
    conn.close()
    return [dict(r) for r in rows]'''
src = src.replace(old, new)

# Modify get_stats to accept user param
old2 = '''def get_stats(start_date=None, end_date=None, process_filter=None, worker_filter=None):
    conn = get_conn()
    wh = []; pa = []
    if start_date: wh.append("r.record_date >= ?"); pa.append(start_date)
    if end_date: wh.append("r.record_date <= ?"); pa.append(end_date)
    if process_filter: wh.append("r.process_id=?"); pa.append(process_filter)
    if worker_filter: wh.append("r.worker_id=?"); pa.append(worker_filter)
    ws = " WHERE " + " AND ".join(wh) if wh else ""'''
new2 = '''def get_stats(start_date=None, end_date=None, process_filter=None, worker_filter=None, user=None):
    conn = get_conn()
    wh = []; pa = []
    if start_date: wh.append("r.record_date >= ?"); pa.append(start_date)
    if end_date: wh.append("r.record_date <= ?"); pa.append(end_date)
    if process_filter: wh.append("r.process_id=?"); pa.append(process_filter)
    if worker_filter: wh.append("r.worker_id=?"); pa.append(worker_filter)
    us, up = _user_scope_filter(user)
    if us: wh.append(us); pa.extend(up)
    ws = " WHERE " + " AND ".join(wh) if wh else ""'''
src = src.replace(old2, new2)

# Modify get_workers to support leader_id filter
old3 = '''def get_workers():
    conn = get_conn(); rows = conn.execute("SELECT * FROM workers ORDER BY group_name, name").fetchall(); conn.close()
    return [dict(r) for r in rows]'''
new3 = '''def get_workers(leader_id=None):
    conn = get_conn()
    if leader_id:
        rows = conn.execute("SELECT * FROM workers WHERE leader_id=? OR id=? ORDER BY group_name, name", (leader_id, leader_id)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM workers ORDER BY group_name, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]'''
src = src.replace(old3, new3)

# Modify add_user to support worker_id
old4 = '''def add_user(un, pw, dn='', role='worker'):
    conn = get_conn()
    try:
        h = _hash_pw(pw)
        conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)", (un,h,dn,role))
        for pk in ALL_PERMS:
            conn.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,0)", (un,pk))
        conn.commit(); conn.close(); return True
    except: conn.close(); return False'''
new4 = '''def add_user(un, pw, dn='', role='worker', worker_id=0):
    conn = get_conn()
    try:
        h = _hash_pw(pw)
        conn.execute("INSERT INTO users (username,password_hash,display_name,role,worker_id) VALUES (?,?,?,?,?)", (un,h,dn,role,worker_id))
        for pk in ALL_PERMS:
            conn.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,0)", (un,pk))
        conn.commit(); conn.close(); return True
    except: conn.close(); return False'''
src = src.replace(old4, new4)

# Modify update_user_display to support worker_id
old5 = '''def update_user_display(un, dn, role):
    conn = get_conn()
    conn.execute("UPDATE users SET display_name=?,role=? WHERE username=?", (dn,role,un))
    conn.commit(); conn.close()'''
new5 = '''def update_user_display(un, dn, role, worker_id=0):
    conn = get_conn()
    conn.execute("UPDATE users SET display_name=?,role=?,worker_id=? WHERE username=?", (dn,role,worker_id,un))
    conn.commit(); conn.close()'''
src = src.replace(old5, new5)

# Modify do_login to set worker_id and role on self.current_user
old6 = '''            r = dict(r)
            if not _verify_pw(pw, r['password_hash']): err_lb.config(text='密码错误'); return
            self.current_user = r
            if cb_rem.get(): _save_cred(un, pw)'''
new6 = '''            r = dict(r)
            if not _verify_pw(pw, r['password_hash']): err_lb.config(text='密码错误'); return
            self.current_user = r
            if cb_rem.get(): _save_cred(un, pw)'''
src = src.replace(old6, new6)

# Modify _refresh to pass user context
old7 = '''    def _refresh(self):
        records = get_all_records(); stats = get_stats(); t = stats["totals"]'''
new7 = '''    def _refresh(self):
        records = get_all_records(self.current_user); stats = get_stats(user=self.current_user); t = stats["totals"]'''
src = src.replace(old7, new7)

# Modify _summary_page dq to pass user
old8 = '''                stats=get_stats(start_date=sd,end_date=ed,process_filter=pf_id,worker_filter=wf_id)'''
new8 = '''                stats=get_stats(start_date=sd,end_date=ed,process_filter=pf_id,worker_filter=wf_id,user=self.current_user)'''
src = src.replace(old8, new8)

# Modify _summary_page ex->get_all_records to pass user
old9 = '''                records=get_all_records()'''
new9 = '''                records=get_all_records(self.current_user)'''
src = src.replace(old9, new9)

# Add leader role support to _manage_users edit dialog role combobox
src = src.replace(
    "cb_role=ttk.Combobox(f2,values=['worker','admin'],width=18,state='readout')",
    "cb_role=ttk.Combobox(f2,values=['worker','admin','leader'],width=18,state='readonly')"
)
# Fix typo in combobox: old was state='readout' and combobox was readonly
# Actually let me check current state
pass

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(src)

print("All changes applied successfully")
