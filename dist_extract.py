"""Extract main.pyc from PyInstaller exe and decompile it."""
import sys
import os
import tempfile
import struct

from PyInstaller.utils.cliutils.archive_viewer import get_archive

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
out_dir = r'C:\Users\Administrator\Documents\Recording\dist_extracted'

os.makedirs(out_dir, exist_ok=True)

archive = get_archive(exe_path)
print(f"Archive type: {type(archive).__name__}")

# List all entries
toc = archive.toc.data
for item in toc:
    name = item[1]
    typecode = item[4]
    print(f"  {typecode}: {name}")

# Extract 'main' entry
print("\n--- Extracting 'main' ---")
data = archive.extract('main')
if data:
    main_pyc_path = os.path.join(out_dir, 'main.pyc')
    with open(main_pyc_path, 'wb') as f:
        f.write(data)
    print(f"Extracted main.pyc ({len(data)} bytes) to {main_pyc_path}")
    
    # Check the pyc header - Python 3.14 has a specific header
    print(f"First 16 bytes: {data[:16].hex()}")
    print(f"First 16 bytes repr: {data[:16]}")
    
    # Python 3.14 pyc header is typically 16 bytes: magic (4) + flags (4) + timestamp (4) + size (4) 
    # But PyInstaller strips the header, we may need to add it back
    # Let's check if it looks like a valid pyc (starts with magic number)
    import importlib.util
    magic = importlib.util.MAGIC_NUMBER
    print(f"Expected magic: {magic.hex()} ({magic})")
    print(f"Data starts with magic: {data[:4] == magic}")
    
    if data[:4] != magic:
        print("PyInstaller strips the pyc header - need to add it back")
        # For Python 3.8+, pyc header is 16 bytes: magic(4) + bitfield(4) + timestamp(4) + size(4)
        # PyInstaller stores just the code object marshalled data after the header
        # Actually, modern PyInstaller stores the full pyc but without the header
        # Let's try to add the header back
        full_pyc = magic + struct.pack('<II', 0, len(data)) + data
        
        # Also try: maybe the data is just the marshalled code object (no header at all)
        # Let's try both approaches
        
        full_pyc_path = os.path.join(out_dir, 'main_full.pyc')
        with open(full_pyc_path, 'wb') as f:
            f.write(full_pyc)
        print(f"Written full pyc with header to {full_pyc_path}")
        
        # Try decompiling
        try:
            import uncompyle6
            out_py = os.path.join(out_dir, 'main.py')
            with open(out_py, 'w', encoding='utf-8') as f:
                uncompyle6.decompile_file(full_pyc_path, f)
            print(f"Decompiled successfully to {out_py}")
        except Exception as e:
            print(f"uncompyle6 failed: {e}")
            
            # Try with pycdc or just marshal.load
            try:
                import marshal
                # Maybe the data IS the marshalled code object
                code = marshal.loads(data)
                print(f"marshal.loads succeeded! Code object: {code}")
                import dis
                dis.dis(code)
            except Exception as e2:
                print(f"marshal.loads also failed: {e2}")
    else:
        # Already has the right header, try decompiling directly
        try:
            import uncompyle6
            out_py = os.path.join(out_dir, 'main.py')
            with open(out_py, 'w', encoding='utf-8') as f:
                uncompyle6.decompile_file(main_pyc_path, f)
            print(f"Decompiled successfully to {out_py}")
        except Exception as e:
            print(f"uncompyle6 failed: {e}")
else:
    print("Failed to extract 'main'")
