import os, importlib
# Test importing the scanner module
for mod_name in ['uncompyle6.scanners.scanner3', 'uncompyle6.scanners.scanner3.14', 'uncompyle6.scanners.scanner3.13']:
    try:
        mod = importlib.import_module(mod_name)
        print(f'OK: {mod_name}')
    except Exception as e:
        print(f'FAIL: {mod_name}: {e}')

# Now try get_scanner directly
import uncompyle6.scanner as s
print(f'\nPYTHON_VERSIONS has (3,14): {(3,14) in s.PYTHON_VERSIONS}')
print(f'CANONIC2VERSION has 3.14: {"3.14" in s.CANONIC2VERSION}')
