import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

# 从 v3.exe 提取
archive = CArchiveReader('ProductionSystem_v3.exe')
data = archive.extract('main')
code = marshal.loads(data)

print(f'Code: {code.co_name}, consts={len(code.co_consts)}')

# 补丁: 在 import scanner3 之前修复 opcode 模块
import xdis.opcodes.opcode_3x.opcode_312 as opc312

# 添加 scanner3 需要的别名  
for missing, actual in [
    ('PJIF', 'POP_JUMP_IF_FALSE'),
    ('PJIT', 'POP_JUMP_IF_TRUE'),
    ('END_FINALLY', 'END_FINALLY'),
    ('SETUP_LOOP', 'SETUP_LOOP'),
    ('CONTINUE_LOOP', 'CONTINUE_LOOP'),
    ('JUMP_ABSOLUTE', 'JUMP_ABSOLUTE'),
    ('BREAK_LOOP', 'BREAK_LOOP'),
    ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_FALSE_OR_POP'),
    ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_TRUE_OR_POP'),
]:
    if not hasattr(opc312, missing) and hasattr(opc312, actual):
        setattr(opc312, missing, getattr(opc312, actual))
        print(f'  Added opc312.{missing}')

import uncompyle6.scanner as scanner_mod
import uncompyle6.semantics.pysource as pysource

# 完全绕过版本检测，直接使用 Scanner3
from uncompyle6.scanners.scanner3 import Scanner3

def simple_get_scanner(version, is_pypy=False, show_asm=None):
    return Scanner3(version, is_pypy, show_asm)

scanner_mod.get_scanner = simple_get_scanner
pysource.get_scanner = simple_get_scanner

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
    # 显示前几行
    for i, line in enumerate(lines[:30]):
        print(f'  {i+1}: {line.rstrip()[:80]}')
