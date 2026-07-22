import marshal, os, sys
from PyInstaller.archive.readers import CArchiveReader

for name in ['ProductionSystem_v3.exe', 'ProductionSystem_v6.exe', 'ProductionSystem_v8.exe',
             'ProductionSystem_v30.exe', 'ProductionSystem_v40.exe', 'ProductionSystem_v39.exe',
             'ProductionSystem_v41.exe']:
    path = os.path.join('dist', name)
    if not os.path.exists(path):
        path = name
    if not os.path.exists(path):
        print(f'{name}: not found')
        continue
    try:
        archive = CArchiveReader(path)
        data = archive.extract('main')
        code = marshal.loads(data)
        # Check Python version from magic
        print(f'{name:35s} constants={len(code.co_consts):4d}  code_len={len(code.co_code):6d}  names={len(code.co_names)}')
    except Exception as e:
        print(f'{name:35s} ERROR: {e}')
