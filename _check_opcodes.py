import xdis.opcodes.opcode_3x.opcode_314 as opc
needed = ['END_FINALLY', 'SETUP_LOOP', 'SETUP_EXCEPT', 'SETUP_FINALLY', 'SETUP_WITH',
          'JUMP_IF_FALSE', 'JUMP_IF_TRUE', 'JUMP_ABSOLUTE', 'BREAK_LOOP', 'CONTINUE_LOOP',
          'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP', 'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
          'CALL_METHOD', 'JUMP_OPs', 'hasvargs', 'CONST_OPS', 'hasjrel', 'hasjabs',
          'LIST_APPEND', 'ROT_TWO', 'GET_ITER', 'COMPARE_OP', 'cmp_op',
          'DUP_TOP', 'ROT_THREE']
with open('_missing_opcodes.txt', 'w', encoding='utf-8') as f:
    for name in needed:
        if hasattr(opc, name):
            f.write(f'OK: {name}={getattr(opc, name)}\n')
        else:
            f.write(f'MISSING: {name}\n')
    # Also list all JUMP-related attrs
    f.write('\n--- All JUMP attrs ---\n')
    for a in dir(opc):
        if 'JUMP' in a or 'POP' in a or 'FINALLY' in a:
            f.write(f'  {a}\n')
print('done')
