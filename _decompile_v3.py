import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

# 从 v3.exe 提取 code object
archive = CArchiveReader('ProductionSystem_v3.exe')
data = archive.extract('main')
code = marshal.loads(data)

print(f'Code: {code.co_name}, consts={len(code.co_consts)}')

# 用 uncompyle6 反编译
import uncompyle6.scanner as scanner_mod
import uncompyle6.semantics.pysource as pysource

# Patch get_scanner for 3.12
orig_get_scanner = scanner_mod.get_scanner
def patched_get_scanner(version, is_pypy=False, show_asm=None):
    try:
        return orig_get_scanner(version, is_pypy, show_asm)
    except (RuntimeError, KeyError) as e:
        from uncompyle6.scanners.scanner3 import Scanner3
        return Scanner3(version, is_pypy, show_asm)

scanner_mod.get_scanner = patched_get_scanner
pysource.get_scanner = patched_get_scanner

# 也确保 scanner.py 有 3.12
scanner_py = os.path.join(os.path.dirname(scanner_mod.__file__), 'scanner.py')
with open(scanner_py, 'r', encoding='utf-8') as f:
    content = f.read()

if '(3, 12)' not in content:
    content = content.replace('(3, 11),', '(3, 11),\n        (3, 12),')
    with open(scanner_py, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py for 3.12')
    import importlib
    importlib.invalidate_caches()

if '"3.12"' not in content:
    content = content.replace('"3.11": (3, 11)', '"3.11": (3, 11),\n    "3.12": (3, 12)')
    with open(scanner_py, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py CANONIC2VERSION for 3.12')

from uncompyle6 import code_deparse
out_path = 'main.py'
with open(out_path, 'w', encoding='utf-8') as f:
    code_deparse(code, f)

size = os.path.getsize(out_path)
with open(out_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'OK: {len(lines)} lines, {size} bytes')

# 验证
import py_compile
try:
    py_compile.compile(out_path, doraise=True)
    print('✅ 编译通过！')
except py_compile.PyCompileError as e:
    print(f'❌ 语法错误: {e}')
