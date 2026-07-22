"""Patch uncompyle6 scanner and decompile ProductionSystem_v30.exe"""
import os, sys, marshal, importlib

# Step 1: Get xdis canonic version for 3.14
from xdis import canonic_python_version
canonic_314 = canonic_python_version['3.14']  # e.g. '3.14rc3'
print(f'xdis canonic for 3.14: {canonic_314!r}')

# Step 2: Check if scanner314.py exists, if not create it from scanner3.py
scanners_dir = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanners'
scanner314_path = os.path.join(scanners_dir, 'scanner314.py')
scanner39_path = os.path.join(scanners_dir, 'scanner39.py')

if not os.path.exists(scanner314_path):
    # Use scanner3.py as the base (most generic Python 3 scanner)
    # scanner3.py class is Scanner3, we need to subclass it as Scanner314
    src_path = os.path.join(scanners_dir, 'scanner3.py')
    with open(src_path, 'r', encoding='utf-8') as f:
        s3 = f.read()
    
    # Create scanner314.py - it should have a Scanner314 class
    # The simplest approach: create a minimal module that imports and re-exports Scanner3
    scanner314_code = '''# Auto-generated scanner for Python 3.14
from uncompyle6.scanners.scanner3 import Scanner3 as Scanner314
'''
    with open(scanner314_path, 'w', encoding='utf-8') as f:
        f.write(scanner314_code)
    print(f'Created scanner314.py')
else:
    print('scanner314.py already exists')

# Step 3: Patch scanner.py
scanner_src = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanner.py'

with open(scanner_src, 'r', encoding='utf-8') as f:
    content = f.read()

# Patch PYTHON_VERSIONS
old_pv = '        (3, 8),\n    )'
new_pv = '        (3, 8),\n        (3, 14),\n    )'
if old_pv in content:
    content = content.replace(old_pv, new_pv)
    print('Patched PYTHON_VERSIONS')

# Patch CANONIC2VERSION - use the actual canonic string
# CANONIC2VERSION is auto-generated from xdis now, so we need to add it manually
old_c2_end = 'CANONIC2VERSION["3.5.2"] = 3.5'
new_c2_entry = f'CANONIC2VERSION["{canonic_314}"] = (3, 14)'
new_c2 = f'{old_c2_end}\n{new_c2_entry}'
if old_c2_end in content:
    content = content.replace(old_c2_end, new_c2)
    print(f'Added CANONIC2VERSION entry for {canonic_314}')
else:
    print(f'WARNING: could not find CANONIC2VERSION anchor')
    idx = content.find('CANONIC2VERSION["3.5.2"]')
    print(f'  Found at index {idx}')

with open(scanner_src, 'w', encoding='utf-8') as f:
    f.write(content)

# Step 4: Patch scanner3.py import (for opcode3x -> base)
scanner3_src = os.path.join(scanners_dir, 'scanner3.py')
if os.path.exists(scanner3_src):
    with open(scanner3_src, 'r', encoding='utf-8') as f:
        s3 = f.read()
    old_imp = 'from xdis.opcodes.opcode3x import parse_fn_counts_30_35'
    if old_imp in s3:
        s3 = s3.replace(old_imp, 'from xdis.opcodes.base import parse_fn_counts_30_35')
        with open(scanner3_src, 'w', encoding='utf-8') as f:
            f.write(s3)
        print('Patched scanner3.py import')

# Step 5: Also check and patch other scanner files that may have the same import
for fn in os.listdir(scanners_dir):
    if fn.endswith('.py') and fn != 'scanner3.py' and not fn.startswith('_'):
        fp = os.path.join(scanners_dir, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            c = f.read()
        if 'from xdis.opcodes.opcode3x' in c:
            c = c.replace('from xdis.opcodes.opcode3x import parse_fn_counts_30_35',
                          'from xdis.opcodes.base import parse_fn_counts_30_35')
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f'Patched {fn} import')

# Step 6: Also need to patch the main parse.py or similar for 3.14 word-level bytecode
# Python 3.14 uses word-level bytecode: instruction_size returns 2
# The scanner needs to handle this. Let's check if xdis handles it.

# Step 7: Reload and import
importlib.invalidate_caches()
for mod in list(sys.modules.keys()):
    if 'uncompyle6' in mod:
        del sys.modules[mod]

import uncompyle6.scanner
print('uncompyle6.scanner imported OK')

# Step 8: Extract and decompile
from PyInstaller.archive.readers import CArchiveReader

exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
print(f'Extracted: {len(data)} bytes')
code = marshal.loads(data)
print(f'Code object: {code.co_name}, filename: {code.co_filename}')

# Step 9: Decompile
from uncompyle6 import code_deparse
out = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(out, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out)
with open(out, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Decompiled: {len(lines)} lines, {size} bytes')

# Step 10: Verify syntax
import py_compile
try:
    py_compile.compile(out, doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
