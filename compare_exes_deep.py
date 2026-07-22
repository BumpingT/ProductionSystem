import os, marshal
from PyInstaller.archive.readers import CArchiveReader

def compare_functions(code1, code2, name="<module>", path=""):
    """Recursively compare two code objects."""
    diffs = []
    # Compare consts
    for i, (c1, c2) in enumerate(zip(code1.co_consts, code2.co_consts)):
        if type(c1) != type(c2):
            diffs.append(f"{path}/{name}: const[{i}] type differs: {type(c1).__name__} vs {type(c2).__name__}")
        elif isinstance(c1, str) and c1 != c2:
            diffs.append(f"{path}/{name}: const[{i}] str differs: {repr(c1)[:50]} vs {repr(c2)[:50]}")
        elif hasattr(c1, 'co_code') and hasattr(c2, 'co_code'):
            sub = compare_functions(c1, c2, c1.co_name or f"<anon_{i}>", f"{path}/{name}")
            diffs.extend(sub)
    
    # Check if lengths differ
    if len(code1.co_consts) != len(code2.co_consts):
        diffs.append(f"{path}/{name}: const count {len(code1.co_consts)} vs {len(code2.co_consts)}")
    if code1.co_names != code2.co_names:
        diffs.append(f"{path}/{name}: names differ")
    if code1.co_code != code2.co_code:
        diffs.append(f"{path}/{name}: BYTECODE DIFFERS ({len(code1.co_code)} vs {len(code2.co_code)} bytes)")
    
    return diffs

v9_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
locked_path = r'C:\Users\Administrator\Documents\Recording\dist\_locked.exe'

# Also compare the PYZ archives (standard library modules)
from PyInstaller.archive.readers import ZlibArchiveReader
import zipfile, io

for label, path in [('v9', v9_path), ('locked', locked_path)]:
    archive = CArchiveReader(path)
    # Check if PYZ.pyz has different content
    pyz_data = archive.extract('PYZ.pyz')
    size = len(pyz_data)
    print(f"{label}: PYZ.pyz = {size} bytes, uncompressed")

# Compare main code
archive_v9 = CArchiveReader(v9_path)
archive_locked = CArchiveReader(locked_path)
data_v9 = archive_v9.extract('main')
data_locked = archive_locked.extract('main')

code_v9 = marshal.loads(data_v9)
code_locked = marshal.loads(data_locked)

print(f"\nV9 main code: {len(data_v9)} bytes")
print(f"Locked main code: {len(data_locked)} bytes")
print(f"Identical bytes: {data_v9 == data_locked}")

diffs = compare_functions(code_v9, code_locked)
if diffs:
    print(f"\nFOUND {len(diffs)} DIFFERENCES:")
    for d in diffs:
        print(f"  {d}")
else:
    print("\nNo differences found in structure or bytecode!")
