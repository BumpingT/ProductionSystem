import os, marshal, struct
from PyInstaller.archive.readers import CArchiveReader

# Try each version to identify the correct one
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

path = 'ProductionSystem_v3.exe'
archive = CArchiveReader(path)
data = archive.extract('main')
code = marshal.loads(data)

print('Testing v3.exe against Python versions:')
for ver in [(3,7), (3,8), (3,9), (3,10), (3,11), (3,12), (3,13), (3,14)]:
    try:
        OPC = get_opcode(ver, PYTHON_IMPLEMENTATION)
        bc = Bytecode(code, OPC)
        instrs = list(bc)
        first = instrs[0].opname if instrs else 'none'
        last = instrs[-1].opname if instrs else 'none'
        # Check if the opcodes make sense - first should always be RESUME or LOAD_CONST
        print(f'  Py{ver[0]}.{ver[1]}: {len(instrs)} instrs, first={first}, last={last}')
        # Show first 3
        ops = [i.opname for i in instrs[:5]]
        print(f'    ops: {ops}')
    except Exception as e:
        print(f'  Py{ver[0]}.{ver[1]}: FAILED - {str(e)[:60]}')
