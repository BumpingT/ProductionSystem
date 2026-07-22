#!/usr/bin/env python3
"""
完整反编译器 — 从 exe 递归反编译所有代码对象，生成可用的 main.py
"""
import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

# ── 加载 exe ──
EXE_PATH = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(EXE_PATH)
data = archive.extract('main')
MODULE_CODE = marshal.loads(data)
OPC = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

EXE_PATH_v40 = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v40.exe'
try:
    archive40 = CArchiveReader(EXE_PATH_v40)
    data40 = archive40.extract('main')
    MODULE_CODE_40 = marshal.loads(data40)
    print('v40 exe loaded')
except:
    MODULE_CODE_40 = None

# 优先用 v40（更新版本）
if MODULE_CODE_40:
    MODULE_CODE = MODULE_CODE_40
    print('Using v40 code')
else:
    print('Using v30 code')

# ── 配置 ──
INDENT = '    '
OUTPUT = []

def out(line='', indent=0):
    OUTPUT.append(INDENT * indent + line)

# ── 递归反编译代码对象 ──
decompiled_cache = {}  # id(code) -> source_lines

def repr_const(c):
    """安全地 repr 常量"""
    if isinstance(c, str):
        return repr(c)
    elif isinstance(c, bytes):
        return repr(c)
    elif c is None:
        return 'None'
    elif isinstance(c, bool):
        return 'True' if c else 'False'
    elif isinstance(c, (int, float)):
        return repr(c)
    elif isinstance(c, tuple):
        if len(c) == 0:
            return '()'
        items = ', '.join(repr_const(x) for x in c)
        if len(c) == 1:
            return f'({items},)'
        return f'({items})'
    else:
        return repr(c)

def decompile_code_obj(co, indent=0):
    """递归反编译一个 code object"""
    cache_key = id(co)
    if cache_key in decompiled_cache:
        return decompiled_cache[cache_key]
    
    local_out = []
    
    # ── 函数签名 ──
    is_module = (co.co_name == '<module>')
    if not is_module:
        args = list(co.co_varnames[:co.co_argcount])
        # 检查是否有 *args 和 **kwargs
        def_argc = co.co_argcount
        sig = ', '.join(args)
        if co.co_flags & 0x04:  # *args
            sig += ', *args'
        if co.co_flags & 0x08:  # **kwargs
            sig += ', **kwargs'
        local_out.append(f'def {co.co_name}({sig}):')
    
    # ── 处理字节码 ──
    try:
        bc = Bytecode(co, OPC)
        instrs = list(bc)
    except:
        local_out.append(f'{INDENT}pass  # bytecode error')
        decompiled_cache[cache_key] = local_out
        return local_out
    
    # 指令序列到源码的映射
    src_lines = {}
    stack = []
    func_defs = []  # 收集嵌套函数定义
    
    i = 0
    while i < len(instrs):
        instr = instrs[i]
        opname = instr.opname
        arg = instr.arg
        argval = instr.argval
        
        line_no = instr.starts_line if instr.starts_line else 0
        
        try:
            if opname in ('RESUME', 'CACHE', 'NOP'):
                pass
            
            elif opname == 'LOAD_CONST':
                if hasattr(argval, 'co_code'):
                    # 嵌套代码对象 — 递归反编译
                    sub = decompile_code_obj(argval, indent + 1)
                    name = argval.co_name
                    stack.append(name)
                    func_defs.extend(sub)
                else:
                    stack.append(repr_const(argval))
            
            elif opname == 'LOAD_SMALL_INT':
                stack.append(str(arg if arg is not None else 0))
            
            elif opname in ('LOAD_FAST', 'LOAD_FAST_BORROW', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                if opname == 'LOAD_FAST_BORROW':
                    name = co.co_varnames[arg] if arg < len(co.co_varnames) else f'var_{arg}'
                elif opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                    name = co.co_names[arg] if arg < len(co.co_names) else f'name_{arg}'
                elif opname == 'LOAD_DEREF':
                    name = co.co_varnames[arg] if arg < len(co.co_varnames) else f'deref_{arg}'
                else:
                    name = co.co_varnames[arg] if arg < len(co.co_varnames) else f'var_{arg}'
                stack.append(name)
            
            elif opname == 'LOAD_ATTR':
                obj = stack.pop() if stack else '???'
                attr = co.co_names[arg] if arg < len(co.co_names) else f'attr_{arg}'
                stack.append(f'{obj}.{attr}')
            
            elif opname == 'STORE_FAST':
                val = stack.pop() if stack else '???'
                name = co.co_varnames[arg] if arg < len(co.co_varnames) else f'var_{arg}'
                src_lines[line_no] = f'{name} = {val}'
            
            elif opname == 'STORE_NAME':
                val = stack.pop() if stack else '???'
                name = co.co_names[arg] if arg < len(co.co_names) else f'name_{arg}'
                src_lines[line_no] = f'{name} = {val}'
            
            elif opname == 'STORE_ATTR':
                val = stack.pop() if stack else '???'
                obj = stack.pop() if stack else '???'
                attr = co.co_names[arg] if arg < len(co.co_names) else f'attr_{arg}'
                src_lines[line_no] = f'{obj}.{attr} = {val}'
            
            elif opname == 'STORE_SUBSCR':
                val = stack.pop() if stack else '???'
                obj = stack.pop() if stack else '???'
                key = stack.pop() if stack else '???'
                src_lines[line_no] = f'{obj}[{key}] = {val}'
            
            elif opname == 'POP_TOP':
                if stack:
                    v = stack.pop()
                    if v and v != 'NULL':
                        src_lines[line_no] = v
            
            elif opname == 'RETURN_VALUE':
                v = stack.pop() if stack else 'None'
                src_lines[line_no] = f'return {v}'
            
            elif opname.startswith('CALL') or opname == 'CALL_METHOD':
                # 调用: 参数数量在 arg 中
                nargs = arg if arg is not None else 0
                call_args = []
                for _ in range(nargs):
                    if stack:
                        call_args.insert(0, stack.pop())
                func = stack.pop() if stack else '???'
                if func == 'NULL':
                    func = stack.pop() if stack else '???'
                stack.append(f'{func}({", ".join(call_args)})')
            
            elif opname == 'CALL_KW':
                npos = arg if arg is not None else 0
                kw_names = stack.pop() if stack else '()'
                args = []
                for _ in range(npos):
                    if stack:
                        args.insert(0, stack.pop())
                func = stack.pop() if stack else '???'
                if func == 'NULL':
                    func = stack.pop() if stack else '???'
                stack.append(f'{func}({", ".join(args)})')
            
            elif opname == 'PUSH_NULL':
                stack.append('NULL')
            
            elif opname == 'BUILD_TUPLE':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                if n == 0:
                    stack.append('()')
                elif n == 1:
                    stack.append(f'({items[0]},)')
                else:
                    stack.append(f'({", ".join(items)})')
            
            elif opname == 'BUILD_LIST':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'[{", ".join(items)}]')
            
            elif opname == 'BUILD_MAP':
                n = arg if arg is not None else 0
                stack.append('{}')
            
            elif opname == 'BUILD_STRING':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'f"{{{", ".join(items)}}}"')
            
            elif opname == 'FORMAT_VALUE':
                pass  # 值已在栈上
            
            elif opname == 'IMPORT_NAME':
                level = stack.pop() if stack else '0'
                fromlist = stack.pop() if stack else '()'
                name = co.co_names[arg] if arg < len(co.co_names) else f'name_{arg}'
                stack.append(f'__import__({repr(name)})')
            
            elif opname == 'IMPORT_FROM':
                name = co.co_names[arg] if arg < len(co.co_names) else f'name_{arg}'
                mod = stack[-1] if stack else '???'
                src_lines[line_no] = f'from {mod} import {name}'
            
            elif opname == 'IMPORT_STAR':
                mod = stack.pop() if stack else '???'
                src_lines[line_no] = f'from {mod} import *'
            
            elif opname in ('MAKE_FUNCTION', 'MAKE_CLOSURE'):
                # 函数的代码对象在上面的 LOAD_CONST 已经处理了
                # 但可能还有默认值等在栈上
                name = stack.pop() if stack else '???'
                # 跳过默认值等
                stack.append(name)
            
            elif opname == 'BUILD_CLASS':
                # 类名在栈上
                methods = stack.pop() if stack else '???'
                bases = stack.pop() if stack else '()'
                name = stack.pop() if stack else '???'
                stack.append(f'type({repr(name)}, {bases}, {{}})')
            
            elif opname == 'UNPACK_SEQUENCE':
                n = arg if arg is not None else 0
                seq = stack.pop() if stack else '???'
                vars_seen = []
                for j in range(n):
                    vars_seen.append(f'var_{j}')
                stack.append(f'({" ,".join(vars_seen)}) = {seq}')
            
            elif opname == 'BINARY_OP' or opname.startswith('BINARY_'):
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                op_map = {'BINARY_OP': '|', 'BINARY_ADD': '+', 'BINARY_SUBTRACT': '-',
                         'BINARY_MULTIPLY': '*', 'BINARY_TRUE_DIVIDE': '/',
                         'BINARY_FLOOR_DIVIDE': '//', 'BINARY_MODULO': '%',
                         'BINARY_POWER': '**', 'BINARY_LSHIFT': '<<', 'BINARY_RSHIFT': '>>',
                         'BINARY_AND': '&', 'BINARY_OR': '|', 'BINARY_XOR': '^'}
                op = op_map.get(opname, '?')
                if opname == 'BINARY_OP':
                    # arg 指定具体操作
                    bin_ops = ['+', '-', '*', '/', '//', '%', '@', '<<', '>>', '&', '^', '|', '**']
                    op = bin_ops[arg] if arg is not None and arg < len(bin_ops) else '?'
                stack.append(f'({left} {op} {right})')
            
            elif opname in ('COMPARE_OP', 'COMPARE_OP_FLOAT'):
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                cmp_ops = ['<', '<=', '==', '!=', '>', '>=', 'in', 'not in', 'is', 'is not']
                op = cmp_ops[arg] if arg is not None and arg < len(cmp_ops) else '?'
                stack.append(f'({left} {op} {right})')
            
            elif opname == 'UNARY_NEGATIVE':
                v = stack.pop() if stack else '???'
                stack.append(f'(-{v})')
            
            elif opname == 'UNARY_NOT':
                v = stack.pop() if stack else '???'
                stack.append(f'(not {v})')
            
            elif opname == 'GET_ITER':
                v = stack.pop() if stack else '???'
                stack.append(f'iter({v})')
            
            elif opname == 'FOR_ITER':
                # stack: iterator, pop it and push items
                pass  # 控制流复杂，暂时跳过
            
            elif opname == 'YIELD_VALUE':
                v = stack.pop() if stack else 'None'
                src_lines[line_no] = f'yield {v}'
            
            elif opname == 'DELETE_FAST':
                name = co.co_varnames[arg] if arg < len(co.co_varnames) else f'var_{arg}'
                src_lines[line_no] = f'del {name}'
            
            elif opname == 'JUMP_FORWARD':
                pass
            
            elif opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE', 'JUMP_IF_FALSE', 'JUMP_IF_TRUE',
                          'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                pass  # 控制流，暂时跳过
            
            elif opname in ('JUMP_BACKWARD', 'JUMP', 'JUMP_ABSOLUTE', 'JUMP_NO_INTERRUPT'):
                pass
            
            elif opname == 'EXTENDED_ARG':
                pass
            
            elif opname == 'NOP':
                pass
            
            elif opname == 'COPY':
                n = arg if arg is not None else 1
                if stack and len(stack) >= n:
                    stack.append(stack[-n])
            
            elif opname == 'SWAP':
                n = arg if arg is not None else 2
                if stack and len(stack) >= n:
                    stack[-1], stack[-n] = stack[-n], stack[-1]
            
            else:
                if not opname.startswith('INSTRUMENTED') and opname not in ('PUSH_EXC_INFO', 'POP_EXCEPT',
                    'SETUP_FINALLY', 'SETUP_EXCEPT', 'SETUP_WITH', 'WITH_CLEANUP',
                    'END_FINALLY', 'PUSH_EXC_INFO', 'RERAISE', 'RAISE_VARARGS',
                    'SETUP_LOOP', 'BREAK_LOOP', 'CONTINUE_LOOP',
                    'POP_BLOCK', 'POP_EXCEPT',
                    'BUILD_SLICE', 'BUILD_SET', 'BUILD_CONST_KEY_MAP',
                    'DICT_UPDATE', 'DICT_MERGE',
                    'LIST_EXTEND', 'SET_ADD', 'MAP_ADD',
                    'LIST_APPEND', 'GET_YIELD_FROM_ITER', 'SEND',
                    'LOAD_BUILD_CLASS', 'LOAD_ASSERTION_ERROR',
                    'GEN_START',  'LOAD_LOCALS', 'LOAD_SUPER_ATTR',
                    'MATCH_KEYS', 'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE',
                    'MATCH_STAR', 'LOAD_ATTR_LOCK', 'BINARY_SUBSCR',
                    'STORE_ATTR_LOCK', 'STORE_SUBSCR_LOCK',
                    'UNPACK_EX',
                    'CONVERT_PRIMITIVE', 'PRIMITIVE_BOX', 'LOAD_FROM_DICT',
                    'STORE_ATTR_ADAPTIVE', 'STORE_SUBSCR_ADAPTIVE', 'LOAD_ATTR_ADAPTIVE',
                    'BINARY_SUBSCR_ADAPTIVE', 'BINARY_SUBSCR_DICT', 'BINARY_SUBSCR_LIST_INT',
                    'BINARY_SUBSCR_TUPLE_INT',
                    'LOAD_ATTR_AADAPTIVE', 'LOAD_ATTR_AADAPTIVE_LOCK',
                    'LOAD_ATTR_INSTANCE_VALUE', 'LOAD_ATTR_MODULE',
                    'LOAD_ATTR_SLOT', 'LOAD_ATTR_WITH_HINT',
                    'STORE_ATTR_INSTANCE_VALUE', 'STORE_ATTR_SLOT',
                    'STORE_ATTR_WITH_HINT',
                    'CALL_BACKWARD', 'CALL_FUNCTION_EX',
                    'CALL_INTRINSIC_1', 'CALL_INTRINSIC_2',
                    'KW_NAMES', 'LOAD_ATTR_METHOD_LAZY_DICT',
                    'LOAD_ATTR_METHOD_NO_DICT', 'LOAD_ATTR_METHOD_WITH_VALUES',
                    'LOAD_ATTR_PROPERTY', 'LOAD_ATTR_CLASS',
                    'LOAD_SUPER_ATTR', 'LOAD_SUPER_ATTR_ATTR', 'LOAD_SUPER_ATTR_METHOD',
                    'PRECALL', 'PRECALL_BOUND', 'PRECALL_BUILTIN_CLASS',
                    'PRECALL_METHOD', 'PRECALL_NO_KW', 'PRECALL_PYFUNC',
                    'PRECALL_TYPE', 'PUSH_NULL', 'STORE_FAST_LOCK',
                    'STORE_FAST_MAYBE', 'LOAD_FAST_AND_CLEAR', 'LOAD_FAST_CHECK',
                    'LOAD_FAST_CHECK', 'LOAD_FAST_LOCK',
                    'LOAD_FROM_DICT_OR_DEREF', 'LOAD_FROM_DICT_OR_GLOBALS',
                    'LOAD_FROM_DICT_OR_LOCALS', 'LOAD_FROM_DICT_OR_NAME',
                    'STORE_FAST_ADAPTIVE', 'BINARY_SLICE', 'STORE_SLICE',
                    'BINARY_OP_ADAPTIVE', 'BINARY_OP_ADD_FLOAT',
                    'BINARY_OP_ADD_INT', 'BINARY_OP_ADD_UNICODE',
                    'BINARY_OP_INPLACE_ADD', 'BINARY_OP_MULTIPLY_FLOAT',
                    'BINARY_OP_MULTIPLY_INT', 'BINARY_OP_SUBTRACT_FLOAT',
                    'BINARY_OP_SUBTRACT_INT',
                    'CONTAINS_OP', 'IS_OP', 'LIST_TO_TUPLE',
                    'LOAD_METHOD', 'LOAD_METHOD_ADAPTIVE',
                    'LOAD_METHOD_CHECK', 'LOAD_METHOD_NO_DICT',
                    'LOAD_METHOD_SUPER', 'LOAD_METHOD_WITH_VALUES',
                    'LOAD_METHOD_CLASS', 'LOAD_METHOD_MODULE',
                    'LOAD_METHOD_PROPERTY', 'LOAD_METHOD_ADAPTIVE_LOCK',
                    'STORE_FAST_MAYBE', 'STORE_FAST_LOCK',
                    'DELETE_FAST_LOCK', 'DELETE_FAST_MAYBE',
                    'CALL', 'CALL_BOUND', 'CALL_BUILTIN_CLASS',
                    'CALL_BUILTIN_FAST', 'CALL_BUILTIN_O', 'CALL_FUNCTION_EX',
                    'CALL_INTRINSIC_1', 'CALL_INTRINSIC_2',
                    'CALL_METHOD_BOUND', 'CALL_METHOD_BUILTIN_CLASS',
                    'CALL_METHOD_BUILTIN_FAST', 'CALL_METHOD_BUILTIN_O',
                    'CALL_METHOD_LEN', 'CALL_METHOD_PY_SIMPLE',
                    'CALL_METHOD_PY_EXTRA', 'CALL_NO_KW',
                    'CALL_NO_KW_BUILTIN_CLASS', 'CALL_NO_KW_BUILTIN_FAST',
                    'CALL_NO_KW_BUILTIN_O', 'CALL_NO_KW_LEN',
                    'CALL_NO_KW_METHOD_BUILTIN_CLASS', 'CALL_NO_KW_METHOD_BUILTIN_FAST',
                    'CALL_NO_KW_METHOD_BUILTIN_O', 'CALL_NO_KW_METHOD_LEN',
                    'CALL_NO_KW_METHOD_PY_SIMPLE', 'CALL_NO_KW_METHOD_PY_EXTRA',
                    'CALL_NO_KW_PY_SIMPLE', 'CALL_NO_KW_PY_EXTRA',
                    'CALL_NO_KW_TYPE_1', 'CALL_PY_EXACT_ARGS',
                    'CALL_PY_EXACT_ARGS_LOCK', 'CALL_PY_GENERAL',
                    'CALL_PY_SIMPLE', 'CALL_PY_WITH_DEFAULTS',
                    'CALL_TYPE', 'CALL_BACKWARD'):
                    pass  # 暂时忽略复杂指令
        
        except Exception as e:
            if opname not in ('RESUME', 'CACHE', 'NOP', 'EXTENDED_ARG'):
                src_lines[line_no] = f'# ERR: {opname}: {e}'
        
        i += 1
    
    # ── 生成源码 ──
    if is_module:
        for line_num in sorted(src_lines.keys()):
            local_out.append(src_lines[line_num])
        # 添加嵌套函数定义
        for fd in func_defs:
            local_out.append('')
            local_out.append(fd)
    else:
        # 函数体
        body_lines = []
        for line_num in sorted(src_lines.keys()):
            body_lines.append(INDENT + src_lines[line_num])
        if not body_lines:
            body_lines.append(INDENT + 'pass')
        local_out.extend(body_lines)
        local_out.extend(func_defs)
    
    decompiled_cache[cache_key] = local_out
    return local_out


# ── 生成 main.py ──
print('正在反编译...')
source_lines = decompile_code_obj(MODULE_CODE, 0)

# 构建最终输出
output = []
output.append('"""')
output.append('生产管理系统 ProductionSystem_v30')
output.append('Decompiled from exe using recursive xdis decompiler')
output.append('"""')
output.append('')

# 添加 import 语句
output.append('import sqlite3, os, sys, webbrowser, tempfile, json, shutil, calendar')
output.append('import hashlib, secrets')
output.append('from datetime import date, timedelta')
output.append('from tkinter import *')
output.append('from tkinter import ttk, messagebox')
output.append('import base64')
output.append('')

# 添加反编译得到的源码
for line in source_lines:
    output.append(line)

# 写文件
with open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f'OK: {len(output)} 行, {len("\\n".join(output).encode("utf-8"))} 字节')

# ── 验证 ──
import py_compile
try:
    py_compile.compile('main.py', doraise=True)
    print('✅ 编译通过！')
except py_compile.PyCompileError as e:
    print(f'❌ 语法错误: {e}')
