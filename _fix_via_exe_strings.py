#!/usr/bin/env python3
"""
从 exe 提取正确字符串，匹配 main.py 中的乱码并修复
"""
import marshal, re, sys
from PyInstaller.archive.readers import CArchiveReader

# ── 1. 提取 exe 中所有正确字符串 ──
exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

correct_strings = []
def walk(co):
    for c in co.co_consts:
        if isinstance(c, str):
            if any('\u4e00' <= ch <= '\u9fff' for ch in c):
                correct_strings.append(c)
        elif hasattr(c, 'co_code'):
            walk(c)
        elif isinstance(c, (tuple, list)):
            for item in c:
                if isinstance(item, str) and any('\u4e00' <= ch <= '\u9fff' for ch in item):
                    correct_strings.append(item)
                elif hasattr(item, 'co_code'):
                    walk(item)

walk(code)
print(f'✅ 从 exe 提取了 {len(correct_strings)} 个正确中文串')

# 去重并按长度排序
correct_strings = sorted(set(correct_strings), key=len, reverse=True)

# ── 2. 读取 main.py ──
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ── 3. 智能替换 ──
# 对每个正确串，尝试在 main.py 中找它的位置
# 由于中文字符被乱码替代，不能直接匹配
# 策略：用正确串中的非中文部分（HTML标签、标点、变量名）做锚点

replace_count = 0
for correct in correct_strings:
    # 如果已经被之前的替换修好了
    if correct in content:
        continue
    
    # 提取非中文部分作为锚点
    # 例如 '（工序筛选：{fl}）' → 锚点: '{fl}', '（', '）', '：'
    ascii_parts = re.findall(r'[\x20-\x7e{}()]+', correct)
    meaningful_anchors = [p for p in ascii_parts if len(p) >= 2]
    
    if not meaningful_anchors:
        continue
    
    # 用最长锚点搜索
    anchors = sorted(meaningful_anchors, key=len, reverse=True)
    
    for anchor in anchors:
        if anchor in content:
            # 找到锚点前后一段文本
            idx = content.index(anchor)
            # 向前后各扩展一些字符
            start = max(0, idx - len(correct))
            end = min(len(content), idx + len(anchor) + len(correct))
            context = content[start:end]
            
            # 检查这段上下文中是否已经有正确串
            if correct in context:
                break  # 已修复
            
            # 尝试替换：用完整正确串替换上下文中的疑似乱码区域
            # 用正则匹配：锚点前后的中文乱码部分
            # 构造正则：([^a-zA-Z]*) + anchor + ([^a-zA-Z]*)
            escaped_anchor = re.escape(anchor)
            pattern = f'(.{{0,{len(correct)}}}){escaped_anchor}(.{{0,{len(correct)}}})'
            m = re.search(pattern, content[start:end])
            if m:
                before = m.group(1)
                after = m.group(2)
                full_match = before + anchor + after
                # 计算相似度
                if len(full_match) >= len(correct) * 0.5 and len(full_match) <= len(correct) * 1.5:
                    new_content = content.replace(full_match, correct)
                    if new_content != content:
                        content = new_content
                        replace_count += 1
                        print(f'  ✓ [{replace_count}] 通过锚点 "{anchor}" 替换了乱码')
                        break
            break

print(f'\n共替换了 {replace_count} 处')

# ── 4. 写回 ──
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已写回 main.py')
