output = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(output, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the missing newline - replace '","seeded","1"))\n    conn.commit()' 
content = content.replace('","seeded","1"))    conn.commit()', '","seeded","1"))\n    conn.commit()')
# Also check if there's a "seeded", "1" variant
content = content.replace('","seeded", "1"))    conn.commit()', '","seeded", "1"))\n    conn.commit()')

with open(output, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed missing newline')
