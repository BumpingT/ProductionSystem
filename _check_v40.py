import marshal
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v40.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

with open('_v40_strings.txt', 'w', encoding='utf-8') as f:
    f.write(f'Module: {code.co_name}, consts={len(code.co_consts)}, code len={len(code.co_code)}\n\n')
    for i, c in enumerate(code.co_consts):
        if isinstance(c, str) and any(ord(ch) > 0x4E00 for ch in c):
            f.write(f'const[{i}] = {repr(c)}\n')
        elif isinstance(c, str) and len(c) > 30:
            f.write(f'const[{i}] (long) = {repr(c)[:100]}\n')

print('done -> _v40_strings.txt')
