"""Analyze bytecode patterns for decompilation"""
import marshal
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
code = marshal.loads(data)
opc = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

# Find the first few simple functions
funcs = []
for const in code.co_consts:
    if hasattr(const, 'co_code') and const.co_name not in ('<lambda>',):
        funcs.append(const)
        if len(funcs) >= 4:
            break

for fn in funcs:
    print(f"\n{'='*70}")
    print(f"FUNCTION: {fn.co_name} (line {fn.co_firstlineno})")
    print(f"Args: {fn.co_varnames[:fn.co_argcount]}")
    print(f"Names: {fn.co_names}")
    print(f"Consts: {[str(c)[:50] for c in fn.co_consts]}")
    print(f"{'='*70}")
    
    bc = Bytecode(fn, opc)
    for instr in bc:
        l = f"L{instr.starts_line}" if instr.starts_line else ""
        jt = " >>" if instr.is_jump_target else "   "
        print(f"{jt} {instr.offset:4d} {l:4s} {instr.opname:30s} arg={instr.arg!r:8s} {str(instr.argval)[:40]}")
