#!/usr/bin/env python3
"""
应急方案：直接从 exe code object 提取字符串常量，生成完整 Python 源码
"""
import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

# 递归提取所有正确字符串
all_correct = set()
code_objects = []

def walk(co, name='<module>'):
    code_objects.append((name, co))
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                all_correct.add(c)
        elif hasattr(c, 'co_code'):
            walk(c, c.co_name)

walk(code)

# 把字符串写入一个引用文件
with open('_correct_strings_all.txt', 'w', encoding='utf-8') as f:
    for s in sorted(all_correct):
        f.write(repr(s) + '\n')

# 输出所有函数的信息
with open('_code_objects.txt', 'w', encoding='utf-8') as f:
    for name, co in code_objects:
        if name == '<module>':
            f.write(f'MODULE: consts={len(co.co_consts)}, names={len(co.co_names)}, code_len={len(co.co_code)}\n')
        else:
            f.write(f'FUNC: {name}(args={co.co_argcount}, consts={len(co.co_consts)}, code_len={len(co.co_code)})\n')
        # 列出顶级常量
        for i, c in enumerate(co.co_consts[:10]):
            if isinstance(c, str):
                f.write(f'  const[{i}] = {repr(c)[:80]}\n')
            elif hasattr(c, 'co_code'):
                f.write(f'  const[{i}] = CODE:{c.co_name}\n')
            else:
                f.write(f'  const[{i}] = {type(c).__name__}:{repr(c)[:50]}\n')

print(f'Correct strings: {len(all_correct)}')
print(f'Code objects: {len(code_objects)}')
print('Wrote _correct_strings_all.txt and _code_objects.txt')
