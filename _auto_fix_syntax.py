#!/usr/bin/env python3
"""
自动修复 main.py 中的所有语法错误（逐轮修复）
"""
import py_compile, sys, re

def try_compile():
    try:
        py_compile.compile('main.py', doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def extract_error_info(err_msg):
    """从错误信息中提取行号和问题描述"""
    m = re.search(r'line (\d+)', err_msg)
    line_no = int(m.group(1)) if m else None
    
    if 'unterminated string' in err_msg or 'unterminated f-string' in err_msg:
        return line_no, 'unterminated_string'
    return line_no, 'unknown'

def fix_unterminated_string(lines, line_no):
    """修复未闭合的字符串"""
    if line_no is None or line_no > len(lines):
        return False
    
    line = lines[line_no - 1]
    # 找这一行中出问题的位置
    # 通常是中文乱码字符导致引号丢失
    # 策略：找到这一行末尾，如果是以乱码字符结尾则加引号
    stripped = line.rstrip()
    
    # 如果行末不是引号，尝试修复
    if not stripped.endswith("'") and not stripped.endswith('"'):
        # 看 f-string 的情况
        if "f'" in stripped or 'f"' in stripped:
            # 在行末加引号
            lines[line_no - 1] = stripped + "'\n"
            return True
        elif "'" in stripped or '"' in stripped:
            # 已有引号，可能在中间某个位置断了
            # 尝试在行末加引号
            lines[line_no - 1] = stripped + "'\n"
            return True
    return False

# 执行修复循环
max_iterations = 50
for iteration in range(max_iterations):
    ok, err = try_compile()
    if ok:
        print(f'🎉 第 {iteration} 轮修复后编译成功！')
        break
    
    print(f'\n=== 第 {iteration+1} 轮 ===')
    print(f'错误: {err}')
    
    line_no, etype = extract_error_info(err)
    if line_no:
        print(f'行号: {line_no}, 类型: {etype}')
    
    with open('main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if etype == 'unterminated_string':
        if fix_unterminated_string(lines, line_no):
            with open('main.py', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f'  ✓ 已修复行 {line_no}')
        else:
            print(f'  ✗ 无法自动修复行 {line_no}')
            # 打印该行内容供参考
            if line_no and line_no <= len(lines):
                print(f'  内容: {repr(lines[line_no-1])}')
            break
    else:
        if line_no and line_no <= len(lines):
            print(f'  行内容: {repr(lines[line_no-1])}')
        break
else:
    print('已达到最大迭代次数')
