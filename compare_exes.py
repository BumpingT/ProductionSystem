"""Compare the two exe files' code structures."""
import os, marshal
from PyInstaller.archive.readers import CArchiveReader

exe_paths = {
    'v9': r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe',
    'locked': r'C:\Users\Administrator\Documents\Recording\dist\_locked.exe',
}

for label, path in exe_paths.items():
    archive = CArchiveReader(path)
    data = archive.extract('main')
    code = marshal.loads(data)
    
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    
    # Module-level names and consts
    print(f"  co_names ({len(code.co_names)}): {code.co_names}")
    print(f"  String consts:")
    for c in code.co_consts:
        if isinstance(c, str) and len(str(c)) < 80:
            print(f"    {repr(c)}")
    
    # List all functions
    print(f"\n  Functions defined:")
    for c in code.co_consts:
        if hasattr(c, 'co_code') and c.co_name != '<lambda>':
            print(f"    [{c.co_name}] line~{c.co_firstlineno}")
            # Also list nested functions
            for c2 in c.co_consts:
                if hasattr(c2, 'co_code') and c2.co_name != '<lambda>':
                    print(f"      => [{c2.co_name}] line~{c2.co_firstlineno}")
