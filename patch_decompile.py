import os, marshal
from PyInstaller.archive.readers import CArchiveReader

# Monkey-patch uncompyle6 version check
import uncompyle6.scanner as scanner
from uncompyle6 import PYTHON3
# The version tuple for Python 3.14.6
import sys
ver_tuple = (3, 14, 6)

# We need to patch the scanner to allow version 3.14
# Let's try to find where the version check is
import uncompyle6.semantics.pysource as pysource
# Monkey-patch code_deparse 
original_code_deparse = pysource.code_deparse

def patched_code_deparse(co, out, **options):
    # Force version detection from the code object itself
    options['is_pypy'] = False
    # Remove version from options and let scanner detect it
    return original_code_deparse(co, out, **options)

# Actually, the issue is in scanner.get_scanner
# Let's patch that directly
original_get_scanner = scanner.get_scanner

def patched_get_scanner(version, is_pypy=False, show_asm=None):
    try:
        return original_get_scanner(version, is_pypy, show_asm)
    except RuntimeError:
        from uncompyle6.scanner import PYTHON3, Scanner3
        if PYTHON3:
            return Scanner3(version, is_pypy, show_asm)
        raise

scanner.get_scanner = patched_get_scanner

exe_path = 'C:\\Users\\Administrator\\Documents\\Recording\\dist\\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

from uncompyle6 import code_deparse
with open(r'C:\Users\Administrator\Documents\Recording\main.py', 'w', encoding='utf-8') as f:
    code_deparse(code, f)

print('Decompiled!')
size = os.path.getsize(r'C:\Users\Administrator\Documents\Recording\main.py')
with open(r'C:\Users\Administrator\Documents\Recording\main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Lines: {len(lines)}, Size: {size} bytes')
