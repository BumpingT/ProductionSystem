output = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(output, 'r', encoding='utf-8') as f:
    content = f.read()

# Add settings table and seeded flag logic to init_db
idx = content.find('    try: c.execute("ALTER TABLE records ADD COLUMN process_id INTEGER")\n    except: pass')
if idx >= 0:
    insert = '\n    # Only seed data once\n    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")\n    seeded = c.execute("SELECT value FROM settings WHERE key=?", ("seeded",)).fetchone()\n    if not seeded:\n'
    content = content[:idx] + insert + content[idx:]
    
    # Add the seeded flag insertion before conn.commit() at end of init_db
    # Find the end of all seed data blocks
    cmt = content.rfind('conn.commit(); conn.close()')
    if cmt > 0:
        # Find the last seed block end
        flag_insert = '\n        c.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", ("seeded","1"))'
        content = content[:cmt] + flag_insert + content[cmt:]
    
    # Adjust indentation for the existing seed code - it needs to be indented 4 more spaces
    # The existing seed blocks need to be under "if not seeded:"
    # Let me check the current structure
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fix applied')
else:
    print('Could not find target text')
