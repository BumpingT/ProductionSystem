#!/usr/bin/env python3
"""
完整的反编译管道 — 修补 opcode + scanner + 反编译
"""
import marshal, os, sys, importlib, re
from PyInstaller.archive.readers import CArchiveReader

# ── 0. 修复 xdis opcode_314 模块 ──
# 在 scanner3 使用 self.opc.PJIF 之前添加别名
import xdis.opcodes.opcode_3x.opcode_314 as opc314
if not hasattr(opc314, 'PJIF'):
    opc314.PJIF = opc314.POP_JUMP_IF_FALSE
    print('Added PJIF alias')
if not hasattr(opc314, 'PJIT'):
    opc314.PJIT = opc314.POP_JUMP_IF_TRUE
    print('Added PJIT alias')

# ── 1. 修复 scanner314.py ──
scanners_dir = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanners'
scanner314_path = os.path.join(scanners_dir, 'scanner314.py')

scanner314_code = '''# Fixed scanner for Python 3.14
from uncompyle6.scanners.scanner3 import Scanner3

class Scanner314(Scanner3):
    def __init__(self, show_asm=None, is_pypy=False, **kwargs):
        super().__init__((3, 14), show_asm, is_pypy)
'''

with open(scanner314_path, 'w', encoding='utf-8') as f:
    f.write(scanner314_code)
print('Fixed scanner314.py')

# ── 2. 修补 scanner.py 版本列表 ──
scanner_py = os.path.join(os.path.dirname(scanners_dir), 'scanner.py')
with open(scanner_py, 'r', encoding='utf-8') as f:
    content = f.read()

modified = False
if '(3, 14)' not in content:
    content = re.sub(
        r'\(\s*3\s*,\s*8\s*\)\s*,',
        '(3, 8),\n        (3, 14),',
        content
    )
    modified = True
if '"3.14"' not in content:
    content = re.sub(
        r'"3\.13":\s*\(3,\s*13\)',
        '"3.13": (3, 13),\n    "3.14": (3, 14)',
        content
    )
    modified = True

if modified:
    with open(scanner_py, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py')
    importlib.invalidate_caches()

# ── 3. 修补 get_scanner ──
import uncompyle6.scanner as scanner_mod
import uncompyle6.semantics.pysource as pysource

orig_get_scanner = scanner_mod.get_scanner
def patched_get_scanner(version, is_pypy=False, show_asm=None):
    try:
        return orig_get_scanner(version, is_pypy, show_asm)
    except (RuntimeError, KeyError, AttributeError) as e:
        print(f'get_scanner fallback: {e}')
        from uncompyle6.scanners.scanner314 import Scanner314
        return Scanner314(version, show_asm, is_pypy)

scanner_mod.get_scanner = patched_get_scanner
pysource.get_scanner = patched_get_scanner

# ── 4. 反编译 ──
exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

print(f'Code: {code.co_name}, size={len(data)} bytes')

from uncompyle6 import code_deparse
out_path = r'C:\Users\Administrator\Documents\Recording\main.py'
with open(out_path, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out_path)
with open(out_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'OK: {len(lines)} lines, {size} bytes')

# ── 5. 验证 ──
import py_compile
try:
    py_compile.compile(out_path, doraise=True)
    print('Syntax: OK!')
except py_compile.PyCompileError as e:
    print(f'Syntax error: {e}')
