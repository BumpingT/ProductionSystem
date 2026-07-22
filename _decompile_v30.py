"""ProductionSystem_v30 decompiler using xdis Bytecode.
Generates Python source from Python 3.14 word-level bytecode."""
import marshal, sys, os, re
from PyInstaller.archive.readers import CArchiveReader
from xdis import Bytecode, get_opcode
from xdis.version_info import PYTHON_IMPLEMENTATION

# ── Load code object ──────────────────────────────────────────────
exe = r'C:\Users\Administrator\Documents\Recording\dist\ProductionSystem_v30.exe'
archive = CArchiveReader(exe)
data = archive.extract('main')
MODULE_CODE = marshal.loads(data)
OPC = get_opcode((3, 14), PYTHON_IMPLEMENTATION)

# ── Instruction grouping helpers ──────────────────────────────────
BINARY_OPS = {
    0: '+', 1: '-', 2: '*', 3: '/', 4: '//', 5: '%',
    6: '@', 7: '<<', 8: '>>', 9: '&', 10: '^', 11: '|',
    12: '**', 13: '+=', 14: '-=', 15: '*=', 16: '/=', 17: '//=',
    18: '%=', 19: '@=', 23: '-=', 24: '**=',
    26: '[]',  # BINARY_SUBSCR
}

COMPARE_OPS = {
    0: '<', 1: '<=', 2: '==', 3: '!=', 4: '>', 5: '>=',
    6: 'in', 7: 'not in', 8: 'is', 9: 'is not',
    18: '<', 19: '<=', 20: '==', 21: '!=', 22: '>', 23: '>=',
    68: 'EXC_MATCH', 70: '<', 71: '<=', 72: '==', 73: '!=',
    74: '>', 75: '>=', 107: 'in', 108: 'not in', 115: 'is',
    116: 'is not', 148: '>', 149: '>=', 172: '>=',
    119: '!=', 174: 'EAGER_',
}

NOFOLLOW = getattr(OPC, 'nofollow', frozenset())

# ── Stack-based expression tracking ──────────────────────────────

class StackMachine:
    """Track stack operations to reconstruct expressions."""
    def __init__(self, code_obj, opc, consts_list):
        self.code = code_obj
        self.opc = opc
        self.consts_list = consts_list
        self.names = code_obj.co_names
        self.varnames = code_obj.co_varnames
        self.stack = []
        self.lines = {}  # line_no -> source_line
        self.current_line = None
        self.scope = 'module'
        self.class_name = None
        self.indent = 0
        self.func_name = code_obj.co_name
        self.instructions = []
        
    def resolve_const(self, idx):
        if idx < len(self.consts_list):
            c = self.consts_list[idx]
            if hasattr(c, 'co_code'):
                return f'<CODE:{c.co_name}>'
            return repr(c)
        return repr(idx)
    
    def resolve_name(self, idx):
        if idx < len(self.names):
            return self.names[idx]
        return f'name#{idx}'
    
    def resolve_varname(self, idx):
        if idx < len(self.varnames):
            return self.varnames[idx]
        return f'var#{idx}'
    
    def emit(self, text=''):
        if self.current_line not in self.lines:
            self.lines[self.current_line] = ''
        old = self.lines[self.current_line]
        indent_str = '    ' * self.indent
        self.lines[self.current_line] = indent_str + text
    
    def append_line(self, text=''):
        self.lines[self.current_line] = text


def extract_consts_list(co):
    """Get a flat list of consts for reference."""
    result = []
    def walk(c):
        result.append(c)
    for c in co.co_consts:
        result.append(c)
    return result


def decompile_code(co, opc, indent=0, scope='module', class_name=None):
    """Decompile a code object into Python source lines."""
    machine = StackMachine(co, opc, list(co.co_consts))
    machine.indent = indent
    machine.scope = scope
    machine.class_name = class_name
    machine.func_name = co.co_name
    
    bc = Bytecode(co, opc)
    instrs = list(bc)
    machine.instructions = instrs
    
    # Build basic block structure
    # First pass: collect jump targets
    jump_targets = set()
    for instr in instrs:
        if instr.is_jump_target:
            jump_targets.add(instr.offset)
        if instr.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
                           'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP', 'JUMP_IF_FALSE', 'JUMP_IF_TRUE'):
            if instr.arg is not None:
                jump_targets.add(instr.arg)
    
    # Second pass: process instructions
    result_lines = []
    stack = []
    indent_level = indent
    
    i = 0
    while i < len(instrs):
        instr = instrs[i]
        off = instr.offset
        
        # Track current line from instruction
        if instr.starts_line:
            machine.current_line = instr.starts_line
        
        opname = instr.opname
        arg = instr.arg
        argval = instr.argval
        
        # ── CACHE instructions are filler, skip ──
        if opname == 'CACHE':
            i += 1
            continue
        
        # ── Handle instruction ──
        try:
            if opname == 'RESUME':
                pass  # No-op at start
            
            elif opname == 'NOP':
                pass
            
            elif opname == 'LOAD_CONST':
                val = repr(argval) if not hasattr(argval, 'co_code') else f'<CODE:{argval.co_name}>'
                stack.append(val)
            
            elif opname == 'LOAD_SMALL_INT':
                stack.append(str(arg))
            
            elif opname == 'LOAD_FAST':
                stack.append(machine.resolve_varname(arg))
            
            elif opname == 'LOAD_FAST_BORROW':
                stack.append(machine.resolve_varname(arg))
            
            elif opname == 'LOAD_FAST_CHECK':
                stack.append(machine.resolve_varname(arg))
            
            elif opname == 'LOAD_FAST_BORROW_LOAD_FAST_BORROW':
                # This is a fused instruction: loads two fast vars
                # arg is a packed value containing two indices
                v1 = machine.resolve_varname(arg & 0xFF)
                v2 = machine.resolve_varname((arg >> 8) & 0xFF)
                stack.append(v1)
                stack.append(v2)
            
            elif opname == 'STORE_FAST_LOAD_FAST':
                v = stack.pop() if stack else '???'
                # Stores one and loads another (fused)
                idx2 = (arg >> 8) & 0xFF
                idx1 = arg & 0xFF
                result_lines.append(('store', machine.current_line or 0, 
                    f'{machine.resolve_varname(idx1)} = {v}'))
                stack.append(machine.resolve_varname(idx2))
            
            elif opname in ('STORE_FAST',):
                v = stack.pop() if stack else '???'
                result_lines.append(('store', machine.current_line or 0,
                    f'{machine.resolve_varname(arg)} = {v}'))
            
            elif opname == 'STORE_NAME':
                v = stack.pop() if stack else '???'
                result_lines.append(('store', machine.current_line or 0,
                    f'{machine.resolve_name(arg)} = {v}'))
            
            elif opname == 'LOAD_FAST_LOAD_FAST':
                # Fused load of two fast locals
                v1 = machine.resolve_varname(arg & 0xFF)
                v2 = machine.resolve_varname((arg >> 8) & 0xFF)
                stack.append(v1)
                stack.append(v2)
            
            elif opname == 'STORE_FAST_STORE_FAST':
                v2 = stack.pop() if stack else '???'
                v1 = stack.pop() if stack else '???'
                idx2 = (arg >> 8) & 0xFF
                idx1 = arg & 0xFF
                result_lines.append(('store', machine.current_line or 0,
                    f'{machine.resolve_varname(idx1)}, {machine.resolve_varname(idx2)} = {v1}, {v2}'))
                stack.append(f'({v1}, {v2})')  # UNPACK_SEQUENCE 2 pushes tuple
            
            elif opname == 'LOAD_GLOBAL':
                stack.append(machine.resolve_name(arg))
            
            elif opname == 'LOAD_NAME':
                stack.append(machine.resolve_name(arg))
            
            elif opname == 'LOAD_DEREF':
                stack.append(machine.resolve_varname(arg))
            
            elif opname == 'LOAD_ATTR':
                obj = stack.pop() if stack else '???'
                stack.append(f'{obj}.{machine.resolve_name(arg)}')
            
            elif opname.startswith('CALL'):
                # CALL instruction: arg is number of args
                # For CALL, args are on stack: func, arg1, arg2, ..., argN
                # But Python 3.14 CALL has PUSH_NULL before function
                nargs = arg if arg is not None else 0
                args = []
                for _ in range(nargs):
                    if stack:
                        args.insert(0, stack.pop())
                func = stack.pop() if stack else '???'
                # Check for PUSH_NULL before function
                if func == 'NULL':
                    func = stack.pop() if stack else '???'
                stack.append(f'{func}({", ".join(args)})')
            
            elif opname == 'CALL_KW':
                # Keyword call: arg is number of positional args
                # Stack: func, pos_args..., kw_keys, kw_call
                npos = arg if arg is not None else 0
                # Last item on stack before call is the keyword tuple
                kw_names = stack.pop() if stack else '()'
                # Parse keyword names
                try:
                    kw_list = eval(kw_names) if kw_names.startswith('(') else []
                except:
                    kw_list = []
                
                args = []
                for _ in range(npos + len(kw_list) if isinstance(kw_list, (tuple, list)) else npos):
                    if stack:
                        args.insert(0, stack.pop())
                func = stack.pop() if stack else '???'
                if func == 'NULL':
                    func = stack.pop() if stack else '???'
                
                if isinstance(kw_list, (tuple, list)) and len(kw_list) > 0:
                    # Split pos_args and kw_args
                    pos_args = args[:-len(kw_list)] if len(args) > len(kw_list) else []
                    kw_args_list = args[-len(kw_list):] if len(args) >= len(kw_list) else []
                    all_args = [str(a) for a in pos_args]
                    for kname, kval in zip(kw_list, kw_args_list):
                        all_args.append(f'{kname}={kval}')
                    stack.append(f'{func}({", ".join(all_args)})')
                else:
                    stack.append(f'{func}({", ".join(str(a) for a in args)})')
            
            elif opname == 'PUSH_NULL':
                stack.append('NULL')
            
            elif opname == 'POP_TOP':
                if stack:
                    v = stack.pop()
                    if v != 'NULL':
                        result_lines.append(('expr', machine.current_line or 0, v))
            
            elif opname == 'RETURN_VALUE':
                v = stack.pop() if stack else 'None'
                result_lines.append(('return', machine.current_line or 0, v))
            
            elif opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE'):
                cond = stack.pop() if stack else '???'
                target = arg if arg is not None else 0
                is_true = opname == 'POP_JUMP_IF_TRUE'
                result_lines.append(('cond', machine.current_line or 0, cond, target, is_true))
            
            elif opname in ('JUMP_FORWARD', 'JUMP', 'JUMP_BACKWARD'):
                target = arg if arg is not None else 0
                result_lines.append(('jump', machine.current_line or 0, target))
            
            elif opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                target = arg if arg is not None else 0
                result_lines.append(('jump', machine.current_line or 0, target))
            
            elif opname == 'FOR_ITER':
                iter_obj = stack.pop() if stack else '???'
                target = arg if arg is not None else 0
                result_lines.append(('for_iter', machine.current_line or 0, iter_obj, target))
            
            elif opname == 'GET_ITER':
                iterable = stack.pop() if stack else '???'
                stack.append(f'iter({iterable})')
            
            elif opname == 'END_FOR':
                pass
            
            elif opname == 'POP_ITER':
                pass
            
            elif opname == 'UNPACK_SEQUENCE':
                seq = stack.pop() if stack else '???'
                n = arg if arg is not None else 0
                vars_list = [f'var_{j}' for j in range(n)]
                result_lines.append(('store', machine.current_line or 0,
                    f'{", ".join(vars_list)} = {seq}'))
            
            elif opname == 'COMPARE_OP':
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                op_type = COMPARE_OPS.get(arg, '??')
                stack.append(f'{left} {op_type} {right}')
            
            elif opname == 'BINARY_OP':
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                op_type = BINARY_OPS.get(arg, f'OP_{arg}')
                if op_type == '[]':
                    stack.append(f'{left}[{right}]')
                elif op_type in ('+=', '-=', '*=', '/=', '%=', '**=', '//=', '@='):
                    stack.append(f'{left} {op_type} {right}')
                else:
                    stack.append(f'{left} {op_type} {right}')
            
            elif opname == 'UNARY_NEGATIVE':
                v = stack.pop() if stack else '???'
                stack.append(f'-{v}')
            
            elif opname == 'UNARY_NOT':
                v = stack.pop() if stack else '???'
                stack.append(f'not {v}')
            
            elif opname == 'BUILD_TUPLE':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'({", ".join(items)}{"," if len(items)==1 else ""})')
            
            elif opname == 'BUILD_LIST':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'[{", ".join(items)}]')
            
            elif opname == 'BUILD_MAP':
                n = arg if arg is not None else 0
                stack.append('{}')
            
            elif opname == 'BUILD_SET':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'{{{", ".join(items)}}}')
            
            elif opname == 'BUILD_STRING':
                n = arg if arg is not None else 0
                items = []
                for _ in range(n):
                    if stack:
                        items.insert(0, stack.pop())
                stack.append(f'f"{{{", ".join(items)}}}"')
            
            elif opname == 'MAP_ADD':
                # MAP_ADD: value is on top, key below
                val = stack.pop() if stack else '???'
                key = stack.pop() if stack else '???'
                d = stack[-1] if stack else '{}'
                # We need to replace the dict on the stack
                # But this is inside a comprehension usually
                stack[-1] = f'{d} | {{{key}: {val}}}'
            
            elif opname == 'LIST_EXTEND':
                items = stack.pop() if stack else '[]'
                lst = stack[-1] if stack else '[]'
            
            elif opname == 'LIST_APPEND':
                val = stack.pop() if stack else '???'
                lst = stack[-1] if stack else '[]'
            
            elif opname == 'SET_ADD':
                val = stack.pop() if stack else '???'
                st = stack[-1] if stack else '{}'
            
            elif opname in ('IMPORT_NAME',):
                stack.pop()  # fromlist
                stack.pop()  # level
                name = machine.resolve_name(arg)
                stack.append(f'__import__({name!r})')
            
            elif opname == 'IMPORT_FROM':
                module = stack[-1] if stack else '???'
                name = machine.resolve_name(arg)
                stack.append(f'{name}')
                result_lines.append(('import_from', machine.current_line or 0, name, module))
            
            elif opname == 'STORE_ATTR':
                val = stack.pop() if stack else '???'
                obj = stack.pop() if stack else '???'
                attr = machine.resolve_name(arg)
                result_lines.append(('store', machine.current_line or 0,
                    f'{obj}.{attr} = {val}'))
            
            elif opname == 'DELETE_FAST':
                pass
            
            elif opname == 'TO_BOOL':
                # pop and push back (truthiness test)
                v = stack[-1] if stack else 'False'
                # stays on stack
            
            elif opname == 'NOT_TAKEN':
                # Hint for optimizer, no effect
                pass
            
            elif opname == 'SWAP':
                n = arg if arg is not None else 2
                if len(stack) >= n:
                    stack[-n], stack[-1] = stack[-1], stack[-n]
            
            elif opname == 'EXTENDED_ARG':
                # Used with high arg values; next instruction's arg is combined
                pass
            
            elif opname == 'COPY':
                n = arg if arg is not None else 1
                if len(stack) >= n:
                    stack.append(stack[-n])
            
            elif opname in ('MAKE_CELL',):
                # v = stack.pop() if stack else '???'
                pass  # MAKE_CELL is just a hint for the runtime
            
            elif opname == 'MAKE_FUNCTION':
                name = stack.pop() if stack else '<lambda>'
                # The function code object is on the stack (or should be)
                stack.append(f'<function {name}>')
            
            elif opname == 'SET_FUNCTION_ATTRIBUTE':
                func = stack.pop() if stack else '<func>'
                flags = arg if arg is not None else 0
                parts = []
                if flags & 1: parts.append('defaults')
                if flags & 2: parts.append('kwdefaults')
                if flags & 4: parts.append('annotations')
                if flags & 8: parts.append('closure')
                stack.append(f'{func}')
            
            elif opname in ('GET_YIELD_FROM_ITER', 'SEND', 'YIELD_VALUE'):
                v = stack.pop() if stack else 'None'
                stack.append(f'yield from/...')
            
            elif opname in ('COPY_FREE_VARS',):
                pass  # Closure setup
            
            elif opname == 'PUSH_EXC_INFO':
                stack.append('<EXC_INFO>')
            
            elif opname == 'POP_EXCEPT':
                stack.pop() if stack else None
            
            elif opname == 'RERAISE':
                result_lines.append(('raise', machine.current_line or 0, ''))
            
            elif opname == 'SETUP_CLEANUP':
                result_lines.append(('try_begin', machine.current_line or 0, arg))
            
            elif opname == 'SETUP_FINALLY':
                result_lines.append(('try_begin', machine.current_line or 0, arg))
            
            elif opname == 'SETUP_WITH':
                ctx = stack.pop() if stack else '???'
                result_lines.append(('with_begin', machine.current_line or 0, ctx, arg))
            
            elif opname == 'POP_BLOCK':
                result_lines.append(('pop_block', machine.current_line or 0))
            
            elif opname == 'ENTER_EXECUTOR':
                pass
            
            elif opname == 'LOAD_BUILD_CLASS':
                stack.append('<BUILD_CLASS>')
            
            elif opname == 'STORE_GLOBAL':
                v = stack.pop() if stack else '???'
                result_lines.append(('store', machine.current_line or 0,
                    f'{machine.resolve_name(arg)} = {v}'))
            
            elif opname in ('DELETE_NAME', 'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR'):
                pass
            
            elif opname == 'CHECK_EXC_MATCH':
                exc = stack.pop() if stack else '???'
                cls = stack.pop() if stack else '???'
                stack.append(f'{exc} matches {cls}')
            
            elif opname == 'CONTAINS_OP':
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                stack.append(f'{left} in {right}')
            
            elif opname == 'IS_OP':
                right = stack.pop() if stack else '???'
                left = stack.pop() if stack else '???'
                stack.append(f'{left} is {right}')
            
            elif opname == 'LOAD_LOCALS':
                stack.append('<locals>')
            
            elif opname == 'LOAD_BUILD_CLASS':
                stack.append('<build_class>')
            
            elif opname in ('GET_AITER', 'GET_ANEXT', 'GET_AWAITABLE', 'SETUP_ANNOTATIONS'):
                pass
            
            elif opname in ('INSTRUMENTED_LINE', 'INSTRUMENTED_RESUME',
                          'INSTRUMENTED_CALL', 'INSTRUMENTED_RETURN_VALUE',
                          'INSTRUMENTED_POP_JUMP_IF_FALSE', 'INSTRUMENTED_POP_JUMP_IF_TRUE',
                          'INSTRUMENTED_JUMP_FORWARD', 'INSTRUMENTED_JUMP_BACKWARD',
                          'INSTRUMENTED_FOR_ITER', 'INSTRUMENTED_END_FOR',
                          'INSTRUMENTED_END_SEND', 'INSTRUMENTED_LOAD_SUPER_ATTR',
                          'INSTRUMENTED_POP_ITER', 'INSTRUMENTED_YIELD_VALUE',
                          'INSTRUMENTED_INSTRUCTION', 'INSTRUMENTED_NOT_TAKEN',
                          'INSTRUMENTED_POP_JUMP_IF_NONE', 'INSTRUMENTED_POP_JUMP_IF_NOT_NONE'):
                pass  # Instrumentation, skip
            
            elif opname == 'CACHE':
                pass
            
            else:
                # Unknown opcode, try to be safe
                result_lines.append(('unknown', machine.current_line or 0, f'# {opname} arg={arg}'))
        
        except Exception as e:
            result_lines.append(('unknown', machine.current_line or 0,
                f'# ERROR at {opname}: {e}'))
        
        i += 1
    
    return result_lines, stack


def format_source(lines, stack, co, indent=0):
    """Format the decompiled lines into Python source."""
    src = []
    indent_str = '    ' * indent
    
    # If this is a function/method, emit signature first
    if co.co_name != '<module>':
        # Determine if it's a method (has 'self' parameter)
        args = list(co.co_varnames[:co.co_argcount])
        if co.co_name != '<lambda>':
            is_method = args and args[0] == 'self'
            if is_method:
                pass
            sig_args = ', '.join(args)
            src.append(f'{indent_str}def {co.co_name}({sig_args}):')
    
    # Process lines
    i = 0
    while i < len(lines):
        line_type = lines[i][0]
        line_no = lines[i][1]
        rest = lines[i][2:]
        
        if line_type == 'store':
            src.append(f'{indent_str}    {rest[0]}')
        
        elif line_type == 'expr':
            expr = rest[0]
            if expr and expr != 'NULL':
                src.append(f'{indent_str}    {expr}')
        
        elif line_type == 'return':
            src.append(f'{indent_str}    return {rest[0]}')
        
        elif line_type == 'import_from':
            name, module = rest
            src.append(f'{indent_str}    from {module} import {name}')
        
        elif line_type == 'cond':
            pass  # Will be handled by control flow analysis
        
        elif line_type == 'jump':
            pass  # Will be handled by control flow analysis
        
        elif line_type == 'for_iter':
            pass
        
        elif line_type == 'unknown':
            src.append(f'{indent_str}    {rest[0]}')
        
        i += 1
    
    return '\n'.join(src)


def generate_main_py():
    """Generate main.py from the code object."""
    co = MODULE_CODE
    opc = OPC
    
    lines = []
    
    # Module header
    lines.append('# Decompiled from ProductionSystem_v30.exe')
    lines.append('# Source: main.py')
    lines.append('# Decompiled using xdis Bytecode decoder')
    lines.append('')
    
    # Process module-level code
    result, stack = decompile_code(co, opc)
    module_src = format_source(result, stack, co, 0)
    lines.append(module_src)
    
    return '\n'.join(lines)


if __name__ == '__main__':
    src = generate_main_py()
    out_path = r'C:\Users\Administrator\Documents\Recording\main.py'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'Written: {len(src)} chars to {out_path}')
