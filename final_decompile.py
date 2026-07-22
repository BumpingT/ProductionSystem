import sys, os, marshal, importlib, py_compile, re
from PyInstaller.archive.readers import CArchiveReader

u = "C:/Users/Administrator/AppData/Local/Programs/Python/Python314/Lib/site-packages/uncompyle6"

for d in ["scanner", "scanners"]:
    dd = os.path.join(u, d)
    if not os.path.isdir(dd): continue
    for fn in os.listdir(dd):
        if not (fn.startswith("scanner3") and fn.endswith(".py")): continue
        fp = os.path.join(dd, fn)
        c = open(fp, "r", encoding="utf-8").read()
        c2 = re.sub(r"import xdis\.opcodes\.opcode_(\w+) as (\w+)", r"from xdis.opcodes import opcode_\1 as \2", c)
        c2 = re.sub(r"import xdis\.opcodes\.opcode(\d+\w*) as (\w+)", r"from xdis.opcodes import opcode_\1 as \2", c2)
        if c2 != c: open(fp, "w", encoding="utf-8").write(c2)
        print("Fixed:", d, fn)

sp = os.path.join(u, "scanner.py")
c = open(sp, "r", encoding="utf-8").read()
if "3.14" not in c:
    c = c.replace('"3.13": (3, 13)', '"3.13": (3, 13),\n    "3.14": (3, 14)')
    c = c.replace("(3, 13),", "(3, 13),\n    (3, 14),")
    open(sp, "w", encoding="utf-8").write(c)
    print("Patched scanner.py")

importlib.invalidate_caches()

# Monkey-patch code_deparse to bypass get_scanner
import uncompyle6.semantics.pysource as ps
import uncompyle6.scanner as sc
from uncompyle6.scanners.scanner3 import scanner3

def patched_gs(version, is_pypy=False, show_asm=None):
    try:
        return sc.get_scanner(version, is_pypy, show_asm)
    except RuntimeError:
        return scanner3(version, is_pypy, show_asm)

ps.get_scanner = patched_gs
sc.get_scanner = patched_gs

from uncompyle6 import code_deparse

exe = "C:/Users/Administrator/Documents/Recording/dist/ProductionSystem_v30.exe"
archive = CArchiveReader(exe)
code = marshal.loads(archive.extract("main"))

with open("main.py", "w", encoding="utf-8") as f:
    code_deparse(code, f)

s = os.path.getsize("main.py")
l = open("main.py").readlines()
print(f"OK: {len(l)} lines, {s} bytes")
py_compile.compile("main.py", doraise=True)
print("Syntax OK")