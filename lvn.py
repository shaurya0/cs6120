import sys
import json
from typing import Tuple, List, Dict, Union
from typing_extensions import TypeAlias

binary_ops = ['add', 'sub', 'mul', 'div']
cmp_ops = ['eq', 'ne', 'lt', 'le', 'gt', 'ge']
logical_ops = ['and', 'or', 'not']

# ('add', 'a', 'b')
# ('const, '3')
# ('mul', 0, 1)
# ...
ExprTuple: TypeAlias = Union[Tuple[str, int], Tuple[str, int, int], Tuple[str, str], Tuple[str, str, str]]
BasicBlock: TypeAlias = List[dict]
class LVNContext:
    def __init__(self):
        self.table :List[ExprTuple,str]  = []
        self.val_idx_map : Dict[str, int] = {}
        self.expr_idx_map : Dict[ExprTuple, int] = {}

    def add(self, expr: ExprTuple, dest: str):
        if len(expr) == 2:
            op, arg = expr
            args = (arg,)
        elif len(expr) == 3:
            op, *args = expr
        else:
            raise ValueError('Invalid expression tuple')

        if expr in self.expr_idx_map:
            idx = self.expr_idx_map[expr]
            self.val_idx_map[dest] = idx
            return

        expr_with_ref = [op]
        for arg in args:
            if arg in self.val_idx_map:
                idx = self.val_idx_map[arg]
                expr_with_ref.append(idx)

        if len(expr_with_ref) != len(expr):
            expr_with_ref.extend(args)

        expr_with_ref = tuple(expr_with_ref)
        self.table.append((expr_with_ref, dest))
        self.val_idx_map[dest] = len(self.table) - 1
        self.expr_idx_map[expr] = len(self.table) - 1



def program_to_basic_blocks(program: dict) -> List[List[dict]]:
    basic_blocks = []
    for function in program['functions']:
        basic_block = []
        for instr in function['instrs']:
            if 'label' in instr:
                if len(basic_block) > 0:
                    basic_blocks.append(basic_block)
                    basic_block = []
                basic_block.append(instr)
            else:
                basic_block.append(instr)

        if len(basic_block) > 0:
            basic_blocks.append(basic_block)
    return basic_blocks

def maybe_get_expr(instr: dict) -> ExprTuple:
    expr = None
    if 'dest' in instr:
        op = instr['op']
        if op == 'const':
            expr = (op, instr['value'])
        elif op == 'not' or op == 'id':
            rhs = instr['args'][0] if 'args' in instr else instr['value']
            expr = (op, rhs)
        elif op in binary_ops or op in cmp_ops or op in logical_ops:
            args = instr['args']
            if op == 'add' or op =='mul':
                # Commutative op
                args = sorted(args)
            expr = (op, args[0], args[1])

    return expr


def get_basic_blocks(program: dict) -> List[Tuple[BasicBlock, LVNContext]]:
    basic_blocks = program_to_basic_blocks(program)
    contexts = []
    for function,bb in zip(program['functions'], basic_blocks):
        context = LVNContext()
        for instr in bb:
            expr = maybe_get_expr(instr)
            if expr is not None:
                context.add(expr, instr['dest'])

        if 'args' in function:
            for arg in function['args']:
                context.add(('id', arg['name']), arg['name'])

        contexts.append(context)

    return list(zip(basic_blocks, contexts))


def common_subexpression_elimination(program: dict, basic_blocks: List[Tuple[BasicBlock, LVNContext]]) -> dict:
    to_remove = []
    for function, (bb, context) in zip(program['functions'], basic_blocks):
        instr_count = 0
        for ii,instr in enumerate(function['instrs']):
            if 'label' in instr:
                instr_count = 0
                continue

            if 'dest' in instr:
                dest = instr['dest']
                var = context.table[context.val_idx_map[dest]][-1]
                if var != dest:
                    instr['args'] = [var]
                    instr['op'] = 'id'

            if 'args' in instr:
                for ii,arg in enumerate(instr['args']):
                    if arg in context.val_idx_map:
                        var = context.table[context.val_idx_map[arg]][-1]
                        if var != arg:
                            instr['args'][ii] = var

            # TODO: this seems flaky
            if 'op' in instr and instr['op'] == 'id' and instr['args'][0] in context.val_idx_map:
                arg = instr['args'][0]
                op, dest = context.table[context.val_idx_map[arg]]
                if op[0] == 'id':
                    src = op[1]

    return program


def constant_folding(program: dict, basic_blocks: List[Tuple[BasicBlock, LVNContext]]) -> dict:
    changed = True
    while changed:
        changed = False
        for function, (bb, context) in zip(program['functions'], basic_blocks):
            for instr in function['instrs']:
                if 'label' in instr:
                    continue
                if instr['op'] in binary_ops or instr['op'] in cmp_ops:
                    arg1 = instr['args'][0]
                    arg2 = instr['args'][1]
                    if arg1 in context.val_idx_map and arg2 in context.val_idx_map:
                        expr1 = context.table[context.val_idx_map[arg1]][0]
                        expr2 = context.table[context.val_idx_map[arg2]][0]
                        if expr1[0] == 'const' and expr2[0] == 'const':
                            val1 = expr1[1]
                            val2 = expr2[1]
                            changed = True
                            if instr['op'] == 'add':
                                instr['op'] = 'const'
                                instr['value'] = val1 + val2
                            elif instr['op'] == 'mul':
                                instr['op'] = 'const'
                                instr['value'] = val1 * val2
                            elif instr['op'] == 'sub':
                                instr['op'] = 'const'
                                instr['value'] = val1 - val2
                            elif instr['op'] == 'div':
                                instr['op'] = 'const'
                                instr['value'] = val1 // val2
                            elif instr['op'] == 'eq':
                                instr['op'] = 'const'
                                instr['value'] = val1 == val2
                            elif instr['op'] == 'neq':
                                instr['op'] = 'const'
                                instr['value'] = val1 != val2
                            elif instr['op'] == 'lt':
                                instr['op'] = 'const'
                                instr['value'] = val1 < val2
                            elif instr['op'] == 'gt':
                                instr['op'] = 'const'
                                instr['value'] = val1 > val2
                            elif instr['op'] == 'le':
                                instr['op'] = 'const'
                                instr['value'] = val1 <= val2
                            elif instr['op'] == 'ge':
                                instr['op'] = 'const'
                                instr['value'] = val1 >= val2
                            else:
                                raise Exception('Unknown op: {}'.format(instr['op']))
                            del instr['args']

                        elif expr1[0] == 'id' and expr2[0] == 'id':
                            val1 = expr1[1]
                            val2 = expr2[1]
                            if val1 == val2:
                                if instr['op'] in ['eq', 'le', 'ge']:
                                    instr['op'] = 'const'
                                    instr['value'] = 'True'
                                    changed = True
                                    del instr['args']
                elif instr['op'] in logical_ops:
                    op = instr['op']
                    if op == 'not':
                        pass
                        rhs = instr['args'][0] if 'args' in instr else instr['value']
                        expr1 = context.table[context.val_idx_map[arg1]][0]
                        if expr1[0] == 'const':
                            changed = True
                            val1 = expr1[1]
                            instr['op'] = 'const'
                            instr['value'] = not val1
                            if 'args' in instr:
                                del instr['args']
                    else:
                        arg1 = instr['args'][0]
                        arg2 = instr['args'][1]
                        expr1 = context.table[context.val_idx_map[arg1]][0]
                        expr2 = context.table[context.val_idx_map[arg2]][0]

                        fold_or_with_const_true = op == 'or' and ((expr1[0] == 'const' and expr2[0] =='id') or (expr1[0] == 'id' and expr2[0] =='const')) and ((expr1[0] == 'const' and expr1[1] == True) or (expr2[0] == 'const' and expr2[1] == True))
                        fold_and_with_const_false = op == 'and' and ((expr1[0] == 'const' and expr2[0] == 'id') or (expr1[0] == 'id' and expr2[0] == 'const')) and (
                            (expr1[0] == 'const' and expr1[1] == False) or (expr2[0] == 'const' and expr2[1] == False))

                        can_fold = (expr1[0] == 'const' and expr2[0] == 'const') or fold_or_with_const_true or fold_and_with_const_false
                        if can_fold:
                            val1 = expr1[1]
                            val2 = expr2[1]
                            del instr['args']

                            changed = True
                            if fold_and_with_const_false:
                                instr['op'] = 'const'
                                instr['value'] = False
                            elif fold_or_with_const_true:
                                instr['op'] = 'const'
                                instr['value'] = True
                            elif op == 'and':
                                instr['op'] = 'const'
                                instr['value'] = val1 and val2
                            elif op == 'or':
                                instr['op'] = 'const'
                                instr['value'] = val1 or val2
                            else:
                                raise Exception('Unknown op: {}'.format(instr['op']))



        if changed:
            basic_blocks = get_basic_blocks(program)

    return program







def main(program: dict) -> dict:
    basic_blocks = get_basic_blocks(program)
    program = common_subexpression_elimination(program, basic_blocks)
    program = constant_folding(program, basic_blocks)
    return program



if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            program = json.load(f)
    else:
        program = sys.stdin.read()
        program = json.loads(program)

    program = main(program)
    print(json.dumps(program))