import os
src = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanner.py'
with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

if '(3, 14)' not in content:
    content = content.replace('(3, 13),', '(3, 13),\n    (3, 14),')
    print('Added (3, 14) to PYTHON_VERSIONS')

key13 = '"3.13": (3, 13)'
key14 = '"3.14": (3, 14)'
if key14 not in content:
    content = content.replace(key13, key13 + ',\n    ' + key14)
    print('Added 3.14 to CANONIC2VERSION')

with open(src, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
