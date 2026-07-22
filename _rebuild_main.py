"""Decompile ProductionSystem_v30.exe - patched version"""
import os, sys, marshal, importlib

# Check xdis canonic version for 3.14
from xdis import canonic_python_version
canonic_314_str = canonic_python_version['3.14']
print(f'xdis canonic for 3.14: {canonic_314_str!r}')

# --- PATCH scanner.py ---
scanner_src = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanner.py'
with open(scanner_src, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add (3,14) to PYTHON_VERSIONS
old_pv = '        (3, 8),\n    )'
new_pv = '        (3, 8),\n        (3, 14),\n    )'
if old_pv in content:
    content = content.replace(old_pv, new_pv)
    print('Patched PYTHON_VERSIONS')
else:
    print('WARNING: could not patch PYTHON_VERSIONS')

# 2. Add canonic version to CANONIC2VERSION
old_c2_end = 'CANONIC2VERSION["3.5.2"] = 3.5'
new_c2 = f'CANONIC2VERSION["{canonic_314_str}"] = (3, 14)'
content = content.replace(old_c2_end, f'{old_c2_end}\n{new_c2}')
print(f'Added CANONIC2VERSION: {canonic_314_str} -> (3, 14)')

# 3. Fix opcode module path for Python 3.14
# The scanner builds: xdis.opcodes.opcode_{v_str} but for 3.x it should be xdis.opcodes.opcode_3x.opcode_{v_str}
old_module = """        if version[:2] in PYTHON_VERSIONS:
            v_str = f\"\"\"opcode_{version_tuple_to_str(version, start=0, end=2, delimiter="")}\"\"\"
            module_name = f\"xdis.opcodes.{v_str}\""""
new_module = """        if version[:2] in PYTHON_VERSIONS:
            v_str = f\"\"\"opcode_{version_tuple_to_str(version, start=0, end=2, delimiter="")}\"\"\"
            # For Python 3.x, xdis 6.x stores opcodes under the opcode_3x subpackage
            if version[0] == 3:
                module_name = f\"xdis.opcodes.opcode_3x.{v_str}\"
            else:
                module_name = f\"xdis.opcodes.{v_str}\""""
if old_module in content:
    content = content.replace(old_module, new_module)
    print('Patched opcode module path for Python 3.x')
else:
    print('WARNING: could not patch opcode module path')
    # Debug: find the exact code
    idx = content.find('v_str = f')
    if idx >= 0:
        print(f'  Found v_str at {idx}: {content[idx:idx+200]}')

with open(scanner_src, 'w', encoding='utf-8') as f:
    f.write(content)

# --- PATCH scanner3.py imports ---
scanners_dir = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanners'
for fn in os.listdir(scanners_dir):
    if fn.endswith('.py') and not fn.startswith('_'):
        fp = os.path.join(scanners_dir, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            c = f.read()
        changed = False
        # Fix any wrong import paths
        for old, new in [
            ('from xdis.opcodes.opcode3x import parse_fn_counts_30_35',
             'from xdis.opcodes.opcode_3x.opcode_3x import parse_fn_counts_30_35'),
            ('from xdis.opcodes.base import parse_fn_counts_30_35',
             'from xdis.opcodes.opcode_3x.opcode_3x import parse_fn_counts_30_35'),
        ]:
            if old in c:
                c = c.replace(old, new)
                changed = True
        if changed:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f'Patched imports in {fn}')

# --- Update scanner314.py ---
scanner314_path = os.path.join(scanners_dir, 'scanner314.py')
with open(scanner314_path, 'w', encoding='utf-8') as f:
    f.write('''# Auto-generated scanner for Python 3.14
import sys
from uncompyle6.scanners.scanner3 import Scanner3

class Scanner314(Scanner3):
    def __init__(self, show_asm=None, is_pypy=False):
        super().__init__((3, 14), show_asm, is_pypy)
''')
print('Updated scanner314.py')

# --- Reload modules ---
importlib.invalidate_caches()
for mod in list(sys.modules.keys()):
    if 'uncompyle6' in mod:
        del sys.modules[mod]

import uncompyle6.scanner
print('uncompyle6.scanner imported OK')

# --- Extract code object ---
from PyInstaller.archive.readers import CArchiveReader

exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
print(f'Extracted: {len(data)} bytes')
code = marshal.loads(data)
print(f'Code object: {code.co_name}')

# --- Decompile ---
from uncompyle6 import code_deparse
out = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(out, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out)
with open(out, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Decompiled: {len(lines)} lines, {size} bytes')

# --- Verify syntax ---
import py_compile
try:
    py_compile.compile(out, doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
