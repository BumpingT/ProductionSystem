#!/usr/bin/env python3
"""
从 exe 提取正确字符串，自动修复 main.py 中的乱码
用法: python _auto_fix_strings.py
"""
import marshal, re, os, sys
from PyInstaller.archive.readers import CArchiveReader

# ── 1. 从 exe 提取所有正确字符串 ──
exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

correct_strings = set()
def walk_consts(co):
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                correct_strings.add(c)
        elif hasattr(c, 'co_code'):
            walk_consts(c)
        elif isinstance(c, (tuple, list)):
            for item in c:
                if isinstance(item, str) and any('\u4e00' <= ch <= '\u9fff' for ch in item):
                    correct_strings.add(item)
                elif hasattr(item, 'co_code'):
                    walk_consts(item)

walk_consts(code)
print(f'从 exe 提取了 {len(correct_strings)} 个正确中文串')

# ── 2. 找出 main.py 中需要修复的地方 ──
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 用 AST 找所有字符串声明位置
# 但由于文件有语法错误，不能用 ast.parse
# 改用正则找字符串常量
issues = []
for correct in correct_strings:
    if correct in content:
        continue  # 这个串是对的
    # 尝试找 corrupted 版本
    # 策略：用 context 匹配
    # 先在 content 中找可能匹配的字符串
    pass

# ── 3. 直接对比法：对每个正确串，找它在 main.py 中最相似的乱码串 ──
import difflib

# 扫描 main.py 中所有被引号括起来的字符串
string_pattern = re.compile(r"""['"](.+?)['"]""", re.DOTALL)
found_in_main = set(m.group(1) for m in string_pattern.finditer(content))

# 对每个正确串，在 found_in_main 中找最长公共子序列匹配
matches = []
for correct in correct_strings:
    best_ratio = 0
    best_match = None
    for candidate in found_in_main:
        if len(candidate) < 2:
            continue
        # 计算相似度
        seq = difflib.SequenceMatcher(None, correct, candidate)
        ratio = seq.ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
    if best_ratio > 0.3 and best_match != correct:
        matches.append((best_match, correct, best_ratio))
        print(f'  匹配: {best_match[:50]!r} → {correct!r} (相似度={best_ratio:.2f})')

# ── 4. 应用替换 ──
print(f'\n共发现 {len(matches)} 个可替换项')
for old, new, ratio in matches:
    if old in content:
        content = content.replace(old, new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'已写回 main.py')
