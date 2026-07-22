import marshal
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)
OPC = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

bc = Bytecode(code, OPC)
instrs = list(bc)

with open('_debug_instr.txt', 'w', encoding='utf-8') as f:
    for instr in instrs[:300]:
        if instr.opname == 'LOAD_CONST':
            argval = instr.argval
            if isinstance(argval, str) and any(ord(c) > 0x4E00 for c in argval):
                val = repr(argval)
                f.write(f'offset={instr.offset} arg={instr.arg} repr={val}\n')
