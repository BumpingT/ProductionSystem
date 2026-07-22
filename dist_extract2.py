"""Extract main.pyc from PyInstaller exe and decompile it."""
import sys, os, struct, marshal, dis, importlib.util

from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
out_dir = r'C:\Users\Administrator\Documents\Recording\dist_extracted'
os.makedirs(out_dir, exist_ok=True)

# Open the CArchive
archive = CArchiveReader(exe_path)
print(f"Options: {archive.options}")

# Extract 'main' entry
data = archive.extract('main')
print(f"Extracted 'main': {len(data)} bytes")

# Check if header is present
magic = importlib.util.MAGIC_NUMBER
print(f"Expected magic: {magic.hex()} ({len(magic)} bytes)")
print(f"Data starts with magic: {data[:len(magic)] == magic}")

pyc_path = os.path.join(out_dir, 'main_original.pyc')
with open(pyc_path, 'wb') as f:
    f.write(data)

if data[:len(magic)] != magic:
    # PyInstaller stores just the marshalled code object after a stripped header
    # For Python 3.8+ the pyc header is 16 bytes (or 12 for older)
    # PyInstaller 6.x uses the full pyc with 16-byte header but may strip it for 's' type
    # Actually, for typecode 's' (source), PyInstaller stores the source as bytes, OR
    # if it's a .pyc it could be the marshalled code object
    
    # Let's try first if it's just a marshalled code object (no header at all)
    try:
        code = marshal.loads(data)
        print(f"\n>>> SUCCESS: marshal.loads() worked!")
        print(f"Code object: {code}")
        print(f"co_name: {code.co_name}")
        print(f"co_filename: {code.co_filename}")
        print(f"co_argcount: {code.co_argcount}, co_nlocals: {code.co_nlocals}, co_stacksize: {code.co_stacksize}")
        print(f"co_consts: {code.co_consts[:10]}...")
        print(f"co_names: {code.co_names}")
        
        # Write disassembly
        with open(os.path.join(out_dir, 'main_dis.txt'), 'w', encoding='utf-8') as f:
            dis.dis(code, file=f)
        
        # Try decompiling with uncompyle6  
        try:
            import uncompyle6
            # Create a valid pyc with header for uncompyle6
            header = magic + struct.pack('<III', 0, 0, len(data))
            full_pyc = header + data
            full_pyc_path = os.path.join(out_dir, 'main.pyc')
            with open(full_pyc_path, 'wb') as f:
                f.write(full_pyc)
            
            out_py = os.path.join(out_dir, 'main.py')
            with open(out_py, 'w', encoding='utf-8') as f:
                uncompyle6.decompile_file(full_pyc_path, f)
            print(f"\n>>> Decompiled successfully to {out_py}")
            print("=" * 60)
            with open(out_py, 'r', encoding='utf-8') as f:
                print(f.read()[:5000])
        except Exception as e:
            print(f"uncompyle6 failed: {e}")
            # Print disassembly instead
            print("\n--- Disassembly (first 200 lines) ---")
            dis.dis(code)
    except Exception as e:
        print(f"marshal.loads failed: {e}")
        
        # Maybe it's a source file (typecode 's')
        try:
            text = data.decode('utf-8')
            print(f"\n>>> Looks like source text! ({len(text)} chars)")
            src_path = os.path.join(out_dir, 'main_source.py')
            with open(src_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(text[:2000])
        except:
            print("Not UTF-8 text either")
            print(f"First 100 bytes hex: {data[:100].hex()}")
else:
    # Has proper header, try decompiling directly
    try:
        import uncompyle6
        out_py = os.path.join(out_dir, 'main.py')
        with open(out_py, 'w', encoding='utf-8') as f:
            uncompyle6.decompile_file(pyc_path, f)
        print(f"Decompiled to {out_py}")
    except Exception as e:
        print(f"uncompyle6 failed: {e}")
