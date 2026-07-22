#!/usr/bin/env python3
"""
从 .pyc 文件反编译（跳过header）
"""
import marshal, os, sys

with open('dist_extracted/main.pyc', 'rb') as f:
    raw = f.read()

code = marshal.loads(raw[16:])
print(f'Code: {code.co_name}, consts={len(code.co_consts)}, file={code.co_filename}')

# 直接输出所有顶级字符串常量和嵌套函数信息
with open('_pyc_info.txt', 'w', encoding='utf-8') as f:
    f.write(f'Filename: {code.co_filename}\n')
    f.write(f'Names: {code.co_names[:20]}\n')
    f.write(f'Varnames: {code.co_varnames[:20]}\n\n')
    
    f.write('=== 顶级常量 ===\n')
    for i, c in enumerate(code.co_consts):
        if isinstance(c, str):
            f.write(f'const[{i}] str = {repr(c)[:100]}\n')
        elif hasattr(c, 'co_code'):
            f.write(f'const[{i}] CODE = {c.co_name}({c.co_argcount} args, {len(c.co_code)} bytes)\n')
        elif isinstance(c, tuple):
            items = [f'{type(x).__name__}:{repr(x)[:30]}' for x in c[:10]]
            f.write(f'const[{i}] tuple({len(c)}) = {items}\n')
        else:
            f.write(f'const[{i}] {type(c).__name__} = {repr(c)[:60]}\n')

print('done')
