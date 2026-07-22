import sqlite3
conn = sqlite3.connect('data.db')
c = conn.cursor()
try:
    rows = c.execute("SELECT * FROM settings").fetchall()
    print("Settings:", rows)
except Exception as e:
    print("Settings error:", e)
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
# Check counts
for t in ['workers','materials','processes','records','users']:
    try:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt}")
    except:
        print(f"  {t}: ERROR")
conn.close()
