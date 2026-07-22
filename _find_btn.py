"""Find and show the bottom bar / _logout section of main.py"""
with open(r'C:\Users\Administrator\Documents\Recording\main.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Search for bottom bar pattern
import re
# Find "修改密码" or "退出登录" buttons
for keyword in ['修改密码', '退出登录', '_logout', '_change_pw', 'bottom bar']:
    idx = src.find(keyword)
    if idx >= 0:
        start = max(0, idx - 200)
        end = min(len(src), idx + 300)
        print(f'--- Found "{keyword}" at pos {idx} ---')
        print(src[start:end])
        print()
        break
else:
    # Show the area near the _logout method
    idx = src.find('def _logout')
    if idx >= 0:
        print(f'--- Near _logout ---')
        print(src[idx-300:idx+500])
