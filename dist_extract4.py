"""Extract main from PyInstaller exe and try marshal + decompile."""
import os, struct, marshal, dis, importlib.util
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
out_dir = r'C:\Users\Administrator\Documents\Recording\dist_extracted'
os.makedirs(out_dir, exist_ok=True)

archive = CArchiveReader(exe_path)
data = archive.extract('main')
print(f"Data: {len(data)} bytes")
print(f"First 32 bytes hex: {data[:32].hex()}")
print(f"First 64 bytes repr: {data[:64]}")

# PyInstaller 's' type for modern PyInstaller (6.x) stores the .pyc content
# but with the header stripped. The remaining data is the marshalled code object.
# For Python 3.14, pyc header is: magic(4) + bitfield(4) + timestamp(4) + filesize(4) = 16 bytes

# Let's see if it starts with a known magic number for a different Python version
# or if it's a marshalled code object directly

# Try marshal.load on entire data
try:
    code = marshal.loads(data)
    print(f"\n>>> marshal.loads on entire data WORKS!")
    print(f"Code: {code}")
except Exception as e:
    print(f"\nmarshal.loads on full data: {e}")
    
    # Try various header sizes
    for header_size in [4, 8, 12, 16, 20, 24]:
        try:
            code = marshal.loads(data[header_size:])
            print(f">>> marshal.loads after {header_size}-byte header WORKS! code={code}")
            break
        except Exception as e2:
            print(f"  header_size={header_size}: {e2}")
    else:
        print("marshal failed for all header sizes")
        exit(1)

print(f"\nCode object details:")
print(f"  co_name: {code.co_name}")
print(f"  co_filename: {code.co_filename}")
print(f"  co_argcount: {code.co_argcount}, co_nlocals: {code.co_nlocals}")
print(f"  co_consts ({len(code.co_consts)}): {code.co_consts[:20]}")
print(f"  co_names ({len(code.co_names)}): {code.co_names}")
print(f"  co_varnames ({len(code.co_varnames)}): {code.co_varnames}")
print(f"  co_freevars: {code.co_freevars}")
print(f"  co_cellvars: {code.co_cellvars}")

# Write disassembly
with open(os.path.join(out_dir, 'main_dis.txt'), 'w', encoding='utf-8') as f:
    dis.dis(code, file=f)
print("Disassembly written to main_dis.txt")

# Try uncompyle6 decompilation
try:
    import uncompyle6
    
    # Need to create valid .pyc file with proper header
    magic = importlib.util.MAGIC_NUMBER  # Python 3.14 magic
    # Python 3.14 header: magic(4) + bitfield(4) + timestamp(4) + size(4) = 16 bytes
    header = magic + struct.pack('<III', 0, 0, len(data))
    full_pyc = header + data
    
    # But if the data already has a partial header, we need to figure out the right approach
    # Let's also try without header if data already is marshalled code
    
    full_pyc_path = os.path.join(out_dir, 'main.pyc')
    with open(full_pyc_path, 'wb') as f:
        f.write(full_pyc)
    
    out_py = os.path.join(out_dir, 'main.py')
    with open(out_py, 'w', encoding='utf-8') as f:
        uncompyle6.decompile_file(full_pyc_path, f)
    print(f"\n>>> uncompyle6 SUCCESS! Output: {out_py}")
    
    # Show the decompiled code
    with open(out_py, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"\n--- Decompiled source ({len(content)} chars) ---")
    print(content[:5000])
    
except Exception as e:
    print(f"\nuncompyle6 failed: {e}")
    # Show disassembly as fallback
    print("\n--- DISASSEMBLY (first 300 lines) ---")
    dis.dis(code)
