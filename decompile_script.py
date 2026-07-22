import os, marshal
from PyInstaller.archive.readers import CArchiveReader
import uncompyle6

exe_path = 'C:\\Users\\Administrator\\Documents\\Recording\\dist\\ProductionSystem_v30.exe'
archive = CArchiveReader(exe_path)
data = archive.extract('main')
code = marshal.loads(data)

with open(r'C:\Users\Administrator\Documents\Recording\main.py', 'w', encoding='utf-8') as f:
    uncompyle6.decompile(code, f, showast=False)

size = os.path.getsize(r'C:\Users\Administrator\Documents\Recording\main.py')
print(f'Decompiled! Size: {size} bytes')
