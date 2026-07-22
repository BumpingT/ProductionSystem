import os, importlib, marshal, py_compile
from PyInstaller.archive.readers import CArchiveReader
from uncompyle6 import code_deparse

u = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Lib\site-packages\uncompyle6"

# Patch scanner3 files - remove underscore from xdis opcode imports
for dname in ["scanner", "scanners"]:
    d = os.path.join(u, dname)
    if not os.path.isdir(d): continue
    for fname in os.listdir(d):
        if fname.startswith("scanner3") and fname.endswith(".py"):
            fp = os.path.join(d, fname)
            c = open(fp, "r", encoding="utf-8").read()
            c = c.replace("xdis.opcodes.opcode_", "xdis.opcodes.opcode")
            open(fp, "w", encoding="utf-8").write(c)
            print("Patched:", dname, fname)

# Update scanner.py
sp = os.path.join(u, "scanner.py")
c = open(sp, "r", encoding="utf-8").read()
old = c
if "\"3.14\"" not in c:
    c = c.replace("\"3.13\": (3, 13)", "\"3.13\": (3, 13),\n    \"3.14\": (3, 14)")
    c = c.replace("(3, 13),", "(3, 13),\n    (3, 14),")
    open(sp, "w", encoding="utf-8").write(c)
    print("Updated scanner.py")

# Decompile v30
exe = r"C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe"
archive = CArchiveReader(exe)
data = archive.extract("main")
code = marshal.loads(data)

importlib.invalidate_caches()
out = r"C:\Users\Administrator\Documents\Recording\main.py"
with open(out, "w", encoding="utf-8") as f:
    code_deparse(code, f)

size = os.path.getsize(out)
lines = open(out, "r").readlines()
print(f"Decompiled: {len(lines)} lines, {size} bytes")
py_compile.compile(out, doraise=True)
print("Syntax: OK")