output = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(output, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire seeding section (from # Only seed data once to conn.commit())
old_start = '    # Only seed data once'
old_end = '    conn.commit(); conn.close()'

start_idx = content.find(old_start)
end_idx = content.find(old_end, start_idx)

old_section = content[start_idx:end_idx]
print(f'Seed section from index {start_idx} to {end_idx}')

new_section = """    # Only seed data once
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    seeded = c.execute("SELECT value FROM settings WHERE key=?", ("seeded",)).fetchone()
    if not seeded:
        c.executemany("INSERT INTO workers (name,group_name) VALUES (?,?)",[('\u5f20\u4e09','\u5207\u5272\u7ec4'),('\u674e\u56db','\u7ec4\u88c5\u7ec4'),('\u738b\u4e94','\u5207\u5272\u7ec4'),('\u8d75\u516d','\u4e0a\u8272\u7ec4'),('\u5b59\u4e03','\u5305\u88c5\u7ec4'),('\u5434\u4e5d','\u68c0\u9a8c\u7ec4')])
        c.executemany("INSERT OR IGNORE INTO materials (name,price) VALUES (?,?)",[('A-1001',5.5),('A-1002',6.0),('B-2001',8.0),('B-2002',8.5),('C-3001',6.0),('C-3002',7.0),('D-4001',12.0),('D-4002',10.0),('E-5001',11.0),('E-5002',9.5)])
        c.executemany("INSERT OR IGNORE INTO processes (material,process_name,unit_price) VALUES (?,?,?)",[('A-1001','\u5207\u5272',1.5),('A-1001','\u6253\u78e8',2.0),('A-1001','\u7ec4\u88c5',1.8),('B-2001','\u5207\u5272',2.0),('B-2001','\u4e0a\u8272',2.5),('B-2001','\u5305\u88c5',1.2),('C-3001','\u5207\u5272',1.8),('C-3001','\u6253\u78e8',2.2),('C-3001','\u7ec4\u88c5',2.0),('D-4001','\u5207\u5272',2.5),('D-4001','\u6253\u78e8',3.0),('D-4001','\u629b\u5149',2.8),('E-5001','\u5207\u5272',3.0),('E-5001','\u7ec4\u88c5',2.5),('E-5001','\u68c0\u9a8c',1.5)])
        c.executemany("INSERT OR IGNORE INTO worker_processes (worker_id,process_id) VALUES (?,?)",[(1,1),(1,2),(1,3),(2,4),(2,5),(3,1),(3,2),(4,5),(4,11),(5,6),(5,8),(6,9),(6,12),(6,15)])
        c.executemany("INSERT INTO records (worker_id,process_id,quantity,unit_price,record_date) VALUES (?,?,?,?,?)",[(1,1,50,1.5,'2026-07-20'),(1,2,30,2.0,'2026-07-20'),(2,4,35,2.5,'2026-07-20'),(3,1,60,1.5,'2026-07-20'),(1,1,40,1.5,'2026-07-21'),(1,3,25,1.8,'2026-07-21'),(2,5,42,1.2,'2026-07-21'),(4,5,28,2.5,'2026-07-21'),(3,2,55,2.0,'2026-07-22'),(5,6,45,1.2,'2026-07-22'),(6,9,32,2.2,'2026-07-22'),(1,2,35,2.0,'2026-07-22'),(2,4,48,2.5,'2026-07-23'),(3,1,62,1.5,'2026-07-23'),(4,11,20,3.0,'2026-07-23'),(5,8,38,1.2,'2026-07-23')])
        c.execute("INSERT INTO settings (key,value) VALUES (?,?)", ("seeded", "1"))
"""

content = content[:start_idx] + new_section + content[end_idx:]

with open(output, 'w', encoding='utf-8') as f:
    f.write(content)

print('Seed section rewritten')
