import sqlite3, os
src = 'dist/data.db'
dst = 'data.db'
print(f'Restoring {src} -> {dst}')
if os.path.exists(dst):
    os.remove(dst)
os.copy(src, dst)

conn = sqlite3.connect(dst)
c = conn.cursor()
with open('_restored_data.txt', 'w', encoding='utf-8') as f:
    f.write('=== 工人 ===\n')
    for r in c.execute('SELECT id, name, group_name FROM workers').fetchall():
        f.write(f'  ID={r[0]} 姓名={r[1]} 组别={r[2]}\n')
    f.write('\n=== 用户 ===\n')
    for r in c.execute('SELECT id, username, display_name, role FROM users').fetchall():
        f.write(f'  ID={r[0]} 账号={r[1]} 显示名={r[2]} 角色={r[3]}\n')
    f.write('\n=== 工序 ===\n')
    for r in c.execute('SELECT id, material, process_name, unit_price FROM processes').fetchall():
        f.write(f'  ID={r[0]} 物料={r[1]} 工序={r[2]} 单价={r[3]}\n')
    f.write('\n=== 记录 ===\n')
    for r in c.execute('SELECT id, worker_id, quantity, record_date FROM records').fetchall():
        f.write(f'  ID={r[0]} 工人ID={r[1]} 件数={r[2]} 日期={r[3]}\n')
conn.close()
print('Written to _restored_data.txt')
