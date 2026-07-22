import marshal, os
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'dist\ProductionSystem_v41.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

def list_functions(co, depth=0):
    funcs = []
    for c in co.co_consts:
        if hasattr(c, 'co_code') and c.co_name != '<module>':
            args = list(c.co_varnames[:c.co_argcount])
            prefix = '  ' * depth
            funcs.append((prefix + c.co_name, args, len(c.co_code)))
            funcs.extend(list_functions(c, depth+1))
    return funcs

funcs = list_functions(code)
for name, args, size in funcs:
    arg_str = ', '.join(args)
    print(f'{name}({arg_str})  [{size} bytes]')

# Also count total functions
print(f'\nTotal: {len(funcs)} functions/methods')
