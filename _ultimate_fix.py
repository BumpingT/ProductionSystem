#!/usr/bin/env python3
"""
最终修复方案：从 exe 提取正确字符串，用上下文锚点匹配修复 main.py
"""
import marshal, re, sys
from PyInstaller.archive.readers import CArchiveReader

# ── 1. 提取正确字符串 ──
exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

correct_all = set()
def walk(co):
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                correct_all.add(c)
        elif hasattr(c, 'co_code'):
            walk(c)
        elif isinstance(c, (tuple, list)):
            for item in c:
                if isinstance(item, str) and any('\u4e00' <= ch <= '\u9fff' for ch in item):
                    correct_all.add(item)
                elif hasattr(item, 'co_code'):
                    walk(item)
walk(code)
print(f'✅ exe中正确中文串: {len(correct_all)}')

# 按长度降序排序（长串优先匹配）
correct_sorted = sorted(correct_all, key=len, reverse=True)

# ── 2. 读取 main.py ──
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 3. 对每个正确串，构建匹配模式并替换 ──
replaced = 0
already_there = 0

for correct in correct_sorted:
    # 如果已经被之前的替换修好了
    if correct in content:
        already_there += 1
        continue
    
    # 提取非中文锚点（ASCII字符、标点、HTML标签、f-string表达式）
    # 策略：用ASCII部分做锚点定位
    parts = re.split(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+', correct)
    ascii_anchors = [p.strip() for p in parts if len(p.strip()) >= 2]
    
    if not ascii_anchors:
        continue
    
    # 用最长的ASCII锚点来定位
    longest_anchor = max(ascii_anchors, key=len)
    escaped = re.escape(longest_anchor)
    
    if longest_anchor not in content:
        continue
    
    # 在锚点周围定位乱码区域
    for m in re.finditer(escaped, content):
        idx = m.start()
        # 向前向后扩展取一个上下文窗口
        window_start = max(0, idx - len(correct) * 2)
        window_end = min(len(content), idx + len(longest_anchor) + len(correct) * 2)
        context = content[window_start:window_end]
        
        # 检查这段上下文是否已包含正确串
        if correct in context:
            continue
        
        # 尝试用正确串替换上下文中的可疑区域
        # 策略：从锚点向两边扩展，直到遇到结构边界（引号、括号、逗号等）
        left = idx - window_start
        right = idx + len(longest_anchor) - window_start
        
        # 向左扩展到最近的 " 或 ' 或 ( 或 , 或 = 
        left_ext = 0
        while left - left_ext > 0:
            ch = context[left - left_ext - 1]
            if ch in ('"', "'", '(', ',', '=', ' ', '\n', '\t', '[', '{', ':', '+', '-', '*', '/'):
                break
            left_ext += 1
            if left_ext > len(correct) * 2:
                break
        
        # 向右扩展到最近的 " 或 ' 或 ) 或 , 或 
        right_ext = 0
        while right + right_ext < len(context):
            ch = context[right + right_ext]
            if ch in ('"', "'", ')', ',', '\n', '\t', ']', '}', ':', '+', '-', '*', '/', ';'):
                break
            right_ext += 1
            if right_ext > len(correct) * 2:
                break
        
        # 提取疑似乱码区域
        suspect = context[left - left_ext:right + right_ext]
        
        # 如果嫌疑区域长度接近正确串长度
        len_ratio = len(suspect) / len(correct) if correct else 0
        if 0.5 <= len_ratio <= 2.0:
            # 替换
            full_context = context.replace(suspect, correct)
            content = content[:window_start] + full_context + content[window_end:]
            replaced += 1
            print(f'  ✓ [{replaced}] 锚点="{longest_anchor[:30]}" | 长度 {len(suspect)}→{len(correct)}')
            break  # 只替换一次

print(f'\n📊 统计: 已存在={already_there}, 新替换={replaced}')

# ── 4. 写回 ──
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ 已写回 main.py')
