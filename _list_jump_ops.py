from xdis import get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

opc = get_opcode((3, 12), PYTHON_IMPLEMENTATION)

# 找出跳转相关的 opcode
jumps = [x for x in dir(opc) if 'JUMP' in x or 'POP' in x or 'FINALLY' in x or 'EXCEPT' in x]
for j in sorted(jumps):
    if j.isupper():
        print(f'  {j} = {getattr(opc, j)}')
