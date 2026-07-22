"""Decompile ProductionSystem_v30.exe using xdis Bytecode"""
import marshal, dis
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
code = marshal.loads(data)
opc = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

def dump_all_code(co, depth=0, name="<module>"):
    prefix = "  " * depth
    bc = Bytecode(co, opc)
    instrs = list(bc)
    
    print(f"{prefix}# {'='*60}")
    print(f"{prefix}# {name} (line {co.co_firstlineno})")
    print(f"{prefix}# Args: {co.co_varnames[:co.co_argcount]}")
    print(f"{prefix}# Locals: {co.co_varnames[co.co_argcount:]}")
    print(f"{prefix}# Names: {co.co_names}")
    print(f"{prefix}# {'='*60}")
    
    # Print all instructions to see control flow
    for instr in instrs:
        line_info = f"L{instr.starts_line}" if instr.starts_line else ""
        jt = " >>" if instr.is_jump_target else "   "
        print(f"{prefix}{jt} {instr.offset:4d} {line_info:4s} {instr.opname:30s} {instr.arg!r:8s} {str(instr.argval)[:30]}")
    
    # Recurse into nested code objects
    for const in co.co_consts:
        if hasattr(const, 'co_code'):
            dump_all_code(const, depth + 1, const.co_name)

dump_all_code(code)
