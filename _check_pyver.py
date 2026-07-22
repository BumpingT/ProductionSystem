import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

# 检查 v3.exe 的 opcode 版本
archive = CArchiveReader(r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v3.exe')
data = archive.extract('main')
code = marshal.loads(data)

# 尝试不同版本的 opcode
for ver in [(3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14)]:
    try:
        OPC = get_opcode(ver, PYTHON_IMPLEMENTATION)
        bc = Bytecode(code, OPC)
        instrs = list(bc)
        # 检查前几条指令是否合理（比如第一指令应该是 RESUME 或 LOAD_CONST）
        first = instrs[0].opname if instrs else 'none'
        print(f'Python {ver}: 第一指令={first}, 总指令数={len(instrs)}')
    except Exception as e:
        print(f'Python {ver}: {e}')
