"""Extract and reconstruct approximate source from PyInstaller exe."""
import os, struct, marshal, dis
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
out_dir = r'C:\Users\Administrator\Documents\Recording\dist_extracted'
os.makedirs(out_dir, exist_ok=True)

archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

# Write disassembly to file (UTF-8 to handle Chinese chars)
import io, sys
old_stdout = sys.stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open(os.path.join(out_dir, 'main_dis.txt'), 'w', encoding='utf-8', errors='replace') as f:
    f.write("=" * 70 + "\n")
    f.write("MODULE: main.py\n")
    f.write("=" * 70 + "\n\n")
    
    def dump_code(co, indent=0):
        prefix = "  " * indent
        if indent == 0:
            f.write(f"{prefix}# Source: {co.co_filename}\n")
            f.write(f"{prefix}# Name: {co.co_name}\n")
            f.write(f"{prefix}# Consts: {repr(co.co_consts[:15])}\n")
            f.write(f"{prefix}# Names: {repr(co.co_names[:30])}\n")
            f.write(f"{prefix}# Varnames: {repr(co.co_varnames[:20])}\n\n")
        
        # Disassemble this code object
        old_dis = dis.dis
        dis_output = io.StringIO()
        # Capture dis output
        try:
            dis.dis(co, file=dis_output)
            f.write(dis_output.getvalue())
        except Exception as e:
            f.write(f"{prefix}# [DIS ERROR: {e}]\n")
        
        f.write("\n")
        
        # Recurse into nested code objects
        for const in co.co_consts:
            if hasattr(const, 'co_code') and const.co_name != '<lambda>':
                f.write(f"\n{prefix}{'─' * 50}\n")
                f.write(f"{prefix}# FUNCTION: {const.co_name} (file: {const.co_filename}, line ~{const.co_firstlineno})\n")
                f.write(f"{prefix}# Args: {const.co_varnames[:const.co_argcount]}\n")
                f.write(f"{prefix}# Consts: {[repr(c)[:60] for c in const.co_consts[:10]]}\n")
                f.write(f"{prefix}{'─' * 50}\n\n")
                dump_code(const, indent + 1)
    
    dump_code(code)

print(f"Disassembly written to {os.path.join(out_dir, 'main_dis.txt')}")

# Also try to create a structural summary
with open(os.path.join(out_dir, 'main_structure.txt'), 'w', encoding='utf-8', errors='replace') as f:
    f.write("STRUCTURAL OVERVIEW of main.py\n\n")
    
    def describe_code(co, indent=0):
        prefix = "  " * indent
        f.write(f"{prefix}[{co.co_name}] file={co.co_filename} line~{co.co_firstlineno}\n")
        f.write(f"{prefix}  Args: {co.co_varnames[:co.co_argcount]}\n")
        f.write(f"{prefix}  Locals: {co.co_varnames[co.co_argcount:]}\n")
        f.write(f"{prefix}  Globals referred: {co.co_names}\n")
        f.write(f"{prefix}  String constants: {[repr(c) for c in co.co_consts if isinstance(c, str)][:20]}\n")
        
        for const in co.co_consts:
            if hasattr(const, 'co_code'):
                describe_code(const, indent + 1)
    
    describe_code(code)

print(f"Structure written to {os.path.join(out_dir, 'main_structure.txt')}")

# Also extract _locked.exe for comparison
exe2_path = r'C:\Users\Administrator\Documents\Recording\dist\_locked.exe'
if os.path.exists(exe2_path):
    out_dir2 = r'C:\Users\Administrator\Documents\Recording\dist_locked'
    os.makedirs(out_dir2, exist_ok=True)
    archive2 = CArchiveReader(exe2_path)
    data2 = archive2.extract('main')
    code2 = marshal.loads(data2)
    
    with open(os.path.join(out_dir2, 'main_dis.txt'), 'w', encoding='utf-8', errors='replace') as f:
        def dump_code2(co, indent=0):
            prefix = "  " * indent
            f.write(f"{prefix}# [{co.co_name}] line~{co.co_firstlineno}\n")
            try:
                dis_output = io.StringIO()
                dis.dis(co, file=dis_output)
                f.write(dis_output.getvalue())
            except Exception as e:
                f.write(f"{prefix}# [DIS ERROR: {e}]\n")
            for const in co.co_consts:
                if hasattr(const, 'co_code') and const.co_name != '<lambda>':
                    dump_code2(const, indent + 1)
        dump_code2(code2)
    
    print(f"Locked exe disassembly written to {out_dir2}")
else:
    print("No _locked.exe found")

print("\nDone!")
