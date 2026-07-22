import os, marshal
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

exes = [
    'ProductionSystem_v3.exe',
    'ProductionSystem_v6.exe',
    'ProductionSystem_v8.exe',
    'dist/ProductionSystem_v30.exe',
    'dist/ProductionSystem_v40.exe',
]

for exe_name in exes:
    if not os.path.exists(exe_name):
        print(f'{exe_name}: not found')
        continue
    archive = CArchiveReader(exe_name)
    data = archive.extract('main')
    code = marshal.loads(data)
    
    # Try each Python version to find the best match
    best_ver = None
    best_count = 0
    for ver in [(3,8), (3,9), (3,10), (3,11), (3,12), (3,13), (3,14)]:
        try:
            OPC = get_opcode(ver, PYTHON_IMPLEMENTATION)
            bc = Bytecode(code, OPC)
            instrs = list(bc)
            if len(instrs) > best_count:
                best_count = len(instrs)
                best_ver = ver
        except:
            pass
    
    # Show details for best version
    try:
        OPC = get_opcode(best_ver, PYTHON_IMPLEMENTATION)
        bc = Bytecode(code, OPC)
        instrs = list(bc)
        first_few = [i.opname for i in instrs[:8]]
        print(f'{exe_name:40s} Py{best_ver[0]}.{best_ver[1]}  {len(instrs):4d} instrs  first={first_few}')
    except Exception as e:
        print(f'{exe_name:40s} ERROR: {e}')
