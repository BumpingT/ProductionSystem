import os
src = r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6\scanner.py'
with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

# Find PYTHON_VERSIONS frozenset 
old_pv = "PYTHON_VERSIONS = frozenset("
# Add (3,14) after (3,13)
old_pv_line_end = ")"

# Also need to update CANONIC2VERSION
old_c2 = "CANONIC2VERSION = dict("
new_c2_line = '    "3.14": 3.14,'

# Replace the frozenset
# Find the line with (3, 13) in PYTHON_VERSIONS
# Pattern: (3, 13),
# Add: (3, 14),
content = content.replace("    (3, 13),\n", "    (3, 13),\n    (3, 14),\n")
# Also add to CANONIC2VERSION if needed  
content = content.replace("    (canonic_python_version[version_tuple_to_str(python_version)], python_version)\n            for python_version in PYTHON_VERSIONS", 
                          "    (canonic_python_version[version_tuple_to_str(python_version)], python_version)\n            for python_version in PYTHON_VERSIONS")

# Check if "3.14" is already in canonic_python_version via xdis
# Also add to canonic_python_version at the bottom
if '"3.14"' not in content:
    # Add after 3.13 entry in canonic
    content = content.replace('"3.13.6": "3.13"', '"3.13.6": "3.13"\n    "3.14.0": "3.14"')
    content = content.replace('"3.13": (3, 13)', '"3.13": (3, 13)\n    "3.14": (3, 14)')

with open(src, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open(src, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '3.14' in line or 'PYTHON_VERSIONS' in line or 'CANONIC2VERSION' in line:
        print(f'{i+1}: {line.rstrip()}')
