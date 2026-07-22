#!/usr/bin/env python3
"""
安全反编译器 — 生成语法正确的 main.py，复杂函数体用 pass 替代
"""
import marshal, os, sys, dis
from PyInstaller.archive.readers import CArchiveReader

# 用 v40 exe（更新）
EXE_PATH = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v40.exe'
if not os.path.exists(EXE_PATH):
    EXE_PATH = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(EXE_PATH)
data = archive.extract('main')
MODULE_CODE = marshal.loads(data)

from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION
OPC = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

# ── 提取所有字符串常量 ──
all_strings = set()
def collect_strings(co):
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                all_strings.add(c)
        elif hasattr(c, 'co_code'):
            collect_strings(c)
        elif isinstance(c, (tuple, list)):
            for item in c:
                if isinstance(item, str) and any('\u4e00' <= ch <= '\u9fff' for ch in item):
                    all_strings.add(item)
                elif hasattr(item, 'co_code'):
                    collect_strings(item)
collect_strings(MODULE_CODE)
print(f'收集到 {len(all_strings)} 个中文字符串')

# ── 写正确字符串参考文件 ──
with open('_correct_strings_all.txt', 'w', encoding='utf-8') as f:
    for s in sorted(all_strings):
        f.write(repr(s) + '\n')

# ── 递归生成代码 ──
INDENT = '    '
OUTPUT = []
output_lines = []

def process_code_obj(co, indent=0):
    """处理代码对象，生成函数定义 + 注释"""
    ind = INDENT * indent
    body_ind = ind + INDENT
    
    is_module = (co.co_name == '<module>')
    
    if not is_module:
        args = list(co.co_varnames[:co.co_argcount])
        sig = ', '.join(args)
        output_lines.append(f'{ind}def {co.co_name}({sig}):')
    
    # 提取该函数中用到的字符串
    func_strings = []
    for c in co.co_consts:
        if isinstance(c, str) and any('\u4e00' <= ch <= '\u9fff' for ch in c):
            func_strings.append(c)
        elif hasattr(c, 'co_code'):
            pass  # 嵌套函数
    
    # 生成简单表达式行
    body_generated = False
    
    # 用 xdis 处理简单指令
    try:
        bc = Bytecode(co, OPC)
        instrs = list(bc)
        
        # 简单模式：只处理最直接的模式（LOAD_CONST + RETURN_VALUE）
        for instr in instrs:
            opname = instr.opname
            arg = instr.arg
            argval = instr.argval
            
            if opname == 'RETURN_VALUE':
                output_lines.append(f'{body_ind}return')
                body_generated = True
            
            elif opname == 'POP_TOP':
                pass
            
            elif opname == 'RESUME':
                pass
            
            elif opname == 'CACHE':
                pass
    except:
        pass
    
    # 输出函数中用到的字符串常量（作为注释）
    if func_strings:
        for s in func_strings[:5]:
            output_lines.append(f'{body_ind}# {repr(s)}')
    if func_strings:
        body_generated = True
    
    # 处理嵌套代码对象
    for c in co.co_consts:
        if hasattr(c, 'co_code') and c.co_name != '<module>' and c != co:
            output_lines.append('')
            process_code_obj(c, indent + 1)
    
    # 如果函数体为空，加 pass
    if not is_module:
        ns = [l for l in output_lines if l.startswith(body_ind)]
        if not ns:
            output_lines.append(f'{body_ind}pass')

# ── 主模块 ──
output_lines.append('import sqlite3, os, sys, webbrowser, tempfile, json, shutil, calendar')
output_lines.append('import hashlib, secrets')
output_lines.append('from datetime import date, timedelta')
output_lines.append('from tkinter import *')
output_lines.append('from tkinter import ttk, messagebox')
output_lines.append('import base64')
output_lines.append('')

# 处理模块级代码 + 递归处理所有嵌套函数
process_code_obj(MODULE_CODE, 0)

# App 类
output_lines.append('')
output_lines.append('class App:')
output_lines.append(f'{INDENT}def __init__(self):')
output_lines.append(f'{INDENT}{INDENT}self.root = None')

# 主入口
output_lines.append('')
output_lines.append('if __name__ == "__main__":')
output_lines.append(f'{INDENT}init_db()')
output_lines.append(f'{INDENT}app = App()')

# 写入文件
header = '''"""
生产管理系统
Auto-generated from exe
"""
'''
full = header + '\n'.join(output_lines)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(full)

print(f'生成 {len(output_lines)} 行, {len(full.encode("utf-8"))} 字节')

# 验证
import py_compile
try:
    py_compile.compile('main.py', doraise=True)
    print('✅ 编译通过！')
except py_compile.PyCompileError as e:
    print(f'❌ 语法错误: {e}')
    print(full[:2000])
