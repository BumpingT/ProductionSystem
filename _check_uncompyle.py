import uncompyle6
print('uncompyle6:', dir(uncompyle6))
import inspect
print('uncompyle6.__version__:', getattr(uncompyle6, '__version__', 'N/A'))
print('uncompyle6.decompile:', getattr(uncompyle6, 'decompile', 'N/A'))
print('uncompyle6.code_deparse:', getattr(uncompyle6, 'code_deparse', 'N/A'))
