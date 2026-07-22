"""Extract main source from PyInstaller exe - 's' typecode = source text."""
import os
from PyInstaller.archive.readers import CArchiveReader

exe_path = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v9.exe'
out_dir = r'C:\Users\Administrator\Documents\Recording\dist_extracted'
os.makedirs(out_dir, exist_ok=True)

archive = CArchiveReader(exe_path)
data = archive.extract('main')

# 's' typecode = source text, stored as bytes
text = data.decode('utf-8')
out_py = os.path.join(out_dir, 'main.py')
with open(out_py, 'w', encoding='utf-8') as f:
    f.write(text)
print(f"Extracted main source ({len(text)} chars) to {out_py}")
print("=" * 70)
print(text[:3000])
