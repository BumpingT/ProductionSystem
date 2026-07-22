import sqlite3

for path, label in [('data.db', '当前'), ('dist/data.db', 'dist备份')]:
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        print(f'\n=== {label} ({path}) ===')
        tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for t in tables:
            name = t[0]
            if name in ('workers','users'):
                cnt = c.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                print(f'  {name}: {cnt} 条')
                rows = c.execute(f"SELECT * FROM {name}").fetchall()
                for r in rows:
                    print(f'    {r}')
        conn.close()
    except Exception as e:
        print(f'{path}: {e}')
