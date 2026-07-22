import shutil, os, marshal
from PyInstaller.archive.readers import CArchiveReader

# Paths
src = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6'

# 1. Create scanner3.14.py
shutil.copy2(os.path.join(src, 'scanner', 'scanner3.py'), os.path.join(src, 'scanner', 'scanner3.14.py'))
print('Created scanner3.14.py')

# 2. Patch scanner.py for 3.14 support
spath = os.path.join(src, 'scanner.py')
with open(spath, 'r', encoding='utf-8') as f:
    content = f.read()

if '3.14' not in content:
    content = content.replace('"3.13": (3, 13)', '"3.13": (3, 13),\n    "3.14": (3, 14)')
    content = content.replace('(3, 13),', '(3, 13),\n    (3, 14),')
    with open(spath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py for 3.14')

# 3. Decompile v30 exe
exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
code = marshal.loads(data)

from uncompyle6 import code_deparse
out = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(out, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out)
with open(out, 'r') as f:
    lines = f.readlines()
print(f'Decompiled: {len(lines)} lines, {size} bytes')

# 4. Verify syntax
import py_compile
py_compile.compile(out, doraise=True)
print('Syntax: OK')
