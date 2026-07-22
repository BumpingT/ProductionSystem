#!/usr/bin/env python3
"""
Simple decompiler - extracts all code objects recursively, generates Python source with correct strings
"""
import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
module_code = marshal.loads(data)

from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION
OPC = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

# ── Recursive decompile ──
output_lines = []

def decompile_func(co, indent=0):
    """Process a function/method code object"""
    ind = '    ' * indent
    lines = []
    
    # Function signature
    args = list(co.co_varnames[:co.co_argcount])
    if co.co_name != '<module>':
        if args and args[0] == 'self':
            sig = ', '.join(args)
        else:
            sig = ', '.join(args)
        lines.append(f'{ind}def {co.co_name}({sig}):')
    
    # Process bytecode
    bc = Bytecode(co, OPC)
    inner_ind = ind + '    '
    
    for instr in bc:
        if instr.opname == 'RESUME':
            continue
        elif instr.opname == 'LOAD_CONST':
            av = instr.argval
            if hasattr(av, 'co_code'):
                # Recursively decompile nested function
                sub = decompile_func(av, indent + 1)
                lines.extend(sub)
            else:
                # String or other constant
                pass  # handled by expression builder
        elif instr.opname == 'RETURN_VALUE':
            lines.append(f'{inner_ind}pass')
            break
    
    if len(lines) == 1:
        lines.append(f'{inner_ind}pass')
    
    return lines

# Top-level module
header = '''"""
生产管理系统 ProductionSystem_v30
Decompiled from ProductionSystem_v30.exe
"""
'''
output_lines.append(header)

# Extract correct strings for reference
correct_strings = set()
def collect_strings(co):
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                correct_strings.add(c)
        elif hasattr(c, 'co_code'):
            collect_strings(c)
        elif isinstance(c, (tuple, list)):
            for item in c:
                if isinstance(item, str) and any('\u4e00' <= ch <= '\u9fff' for ch in item):
                    correct_strings.add(item)
                elif hasattr(item, 'co_code'):
                    collect_strings(item)

collect_strings(module_code)

# Write correct strings reference
with open('_correct_strings_all.txt', 'w', encoding='utf-8') as f:
    for s in sorted(correct_strings):
        f.write(repr(s) + '\n')

# Write function stubs
func_count = 0
def list_funcs(co, name='<module>'):
    global func_count
    for c in co.co_consts:
        if hasattr(c, 'co_code') and c.co_name != '<module>':
            func_count += 1
            args = ', '.join(list(c.co_varnames[:c.co_argcount]))
            output_lines.append(f'def {c.co_name}({args}):')
            output_lines.append(f'    pass')
            output_lines.append('')
            list_funcs(c, c.co_name)

output_lines.append('import sqlite3, os, sys, webbrowser, tempfile, json, shutil, calendar')
output_lines.append('import hashlib, secrets')
output_lines.append('from datetime import date, timedelta')
output_lines.append('from tkinter import *')
output_lines.append('from tkinter import ttk, messagebox')
output_lines.append('import base64')
output_lines.append('')
list_funcs(module_code)

# Add class App stub
output_lines.append('class App:')
output_lines.append('    def __init__(self):')
output_lines.append('        pass')
output_lines.append('')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f'OK: {func_count} functions, {len(output_lines)} lines')
print(f'Correct strings: {len(correct_strings)} (saved to _correct_strings_all.txt)')
