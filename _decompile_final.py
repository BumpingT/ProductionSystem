#!/usr/bin/env python3
"""
修复版 uncompyle6 反编译脚本
"""
import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

# ── 1. 确保 scanner 支持 3.14 ──
import uncompyle6.scanner as scanner_mod
import uncompyle6.semantics.pysource as pysource

# 修补 get_scanner
orig_get_scanner = scanner_mod.get_scanner

def patched_get_scanner(version, is_pypy=False, show_asm=None):
    try:
        return orig_get_scanner(version, is_pypy, show_asm)
    except (RuntimeError, KeyError):
        from uncompyle6.scanners.scanner3 import Scanner3
        return Scanner3(version, is_pypy, show_asm)

scanner_mod.get_scanner = patched_get_scanner
pysource.get_scanner = patched_get_scanner

# ── 2. 也修补 scanner.py 中的版本列表 ──
scanner_py = os.path.join(os.path.dirname(scanner_mod.__file__), 'scanner.py')
with open(scanner_py, 'r', encoding='utf-8') as f:
    content = f.read()

modified = False
if '(3, 14)' not in content:
    content = content.replace('(3, 13),', '(3, 13),\n        (3, 14),')
    modified = True
if '"3.14"' not in content:
    content = content.replace('"3.13": (3, 13)', '"3.13": (3, 13),\n    "3.14": (3, 14)')
    modified = True

if modified:
    with open(scanner_py, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py for 3.14')
    import importlib
    importlib.invalidate_caches()

# ── 3. 反编译 ──
exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

print(f'Code object: {code.co_name}, consts={len(code.co_consts)}')

from uncompyle6 import code_deparse
out_path = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(out_path, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out_path)
with open(out_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'OK: {len(lines)} lines, {size} bytes')

# ── 4. 验证 ──
import py_compile
try:
    py_compile.compile(out_path, doraise=True)
    print('Syntax: OK!')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
