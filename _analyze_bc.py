"""Analyze v30 exe bytecode using xdis"""
import marshal
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
code = marshal.loads(data)

print(f'Module: {code.co_name}')
print(f'co_code length: {len(code.co_code)}')
print(f'Python impl: {PYTHON_IMPLEMENTATION}')

# Get opcode module for Python 3.14
opc = get_opcode((3, 14), PYTHON_IMPLEMENTATION)
print(f'opc: {opc}')
print(f'opc type: {type(opc)}')

# Get instructions
bc = Bytecode(code, opc)
instrs = list(bc)
print(f'Total instructions: {len(instrs)}')
print(f'\nFirst 25 instructions:')
for i, instr in enumerate(instrs[:25]):
    print(f'  {i}: {instr}')
