import os, marshal, sys
from PyInstaller.archive.readers import CArchiveReader

# Directly patch scanner.py's version check
import uncompyle6.scanner as scanner_mod
import inspect

src = inspect.getfile(scanner_mod)
print(f'Scanner file: {src}')

# Read the scanner file
with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the version check function
# The get_scanner function has a version check
# We need to add 3.14 to the supported versions

# Check what versions are supported
# Find the part that checks for version 3.11, 3.12, 3.13
old = "3.13"
new = "3.13, 3.14"
if old in content:
    content = content.replace(old, new)
    with open(src, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched scanner.py to add Python 3.14 support')
else:
    print('3.13 not found in scanner.py')
    # Check if there's a version tuple list
    for line in content.split('\n'):
        if '3.13' in line or '3.14' in line or 'SUPPORTED' in line or 'version' in line.lower():
            print(f'  Found: {line.strip()}')
