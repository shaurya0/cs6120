import sys
import json
from typing import Tuple, List, Dict, Set
from dominators import program_to_basic_blocks, BasicBlock, get_dominance_frontier, get_dominance_tree, get_dominators


def get_globals(blocks: Dict[str, BasicBlock]) -> Tuple[set, dict]:
    globals = set()
    defs = dict()
    for block_label, block in blocks.items():
        var_kill = set()
        for instr in block.instrs:
            if 'op' in instr and 'dest' in instr:
                dest = instr['dest']
                globals.add(dest)
                if 'args' in instr:
                    for arg in instr['args']:
                        if arg not in var_kill:
                            globals.add(arg)

                var_kill.add(dest)
                if dest in defs:
                    defs[dest].add(block_label)
                else:
                    defs[dest] = set([block_label])
    return globals, defs


def insert_phi_functions(globals, definitions, dominance_frontier, blocks: Dict[str, BasicBlock]) -> None:
    for var in globals:
        work_list = list(definitions[var])
        for block in work_list:
            for frontier_block_label in dominance_frontier[block]:
                frontier_block = blocks[frontier_block_label]
                phi_instr_found = False
                for instr in frontier_block.instrs:
                    if 'op' in instr and instr['op'] == 'phi' and instr['dest'] == var:
                        phi_instr_found = True
                        break

                if not phi_instr_found:
                    phi_instr = {
                        'op': 'phi',
                        'dest': var,
                        'type': 'int',
                        'labels': [block],
                        'args': [var]
                    }
                    frontier_block.instrs.insert(0, phi_instr)
                    work_list.append(frontier_block.label)
                else:
                    phi_instr = instr
                    phi_instr['labels'].append(block)
                    phi_instr['args'].append(var)



def rename_ssa(blocks: Dict[str, BasicBlock], globals_: Set[str], dom_tree: Dict[str, List[str]]):
    counter = {}
    stack = {}

    def newname(n):
        i = counter[n]
        counter[n] += 1
        stack[n].insert(0, i)
        return f'{n}.{i}'

    def rename_block(block: BasicBlock):
        for instr in block.instrs:
            if 'op' in instr and instr['op'] == 'phi':
                dest = instr['dest'].split('.')[0]
                instr['dest'] = newname(dest)

        for instr in block.instrs:
            if 'op' in instr and instr['op'] == 'phi':
                continue

            if 'args' in instr:
                for i, arg in enumerate(instr['args']):
                    a = arg.split('.')[0]
                    if a not in globals_:
                        break
                    instr['args'][i] = f'{a}.{stack[a][0]}'

            if 'dest' in instr:
                dest = instr['dest'].split('.')[0]
                instr['dest'] = newname(dest)



        for successor_label in dom_tree[block.label]:
            successor = blocks[successor_label]

            for instr in successor.instrs:
                if 'op' in instr and instr['op'] == 'phi':
                    for i, arg in enumerate(instr['args']):
                        a = arg.split('.')[0]
                        instr['args'][i] = f'{a}.{stack[a][0]}'
                    dest = instr['dest'].split('.')[0]
                    instr['dest'] = f'{dest}.{stack[dest][0]}'

        for successor_label in block.successors:
            successor = blocks[successor_label]
            rename_block(successor)


        for instr in block.instrs:
            if 'op' in instr and instr['op'] == 'phi':
                dest = instr['dest'].split('.')[0]
                stack[dest].pop(0)

            if 'dest' in instr:
                dest = instr['dest'].split('.')[0]
                stack[dest].pop(0)

    for n in globals_:
        counter[n] = 1
        stack[n] = []

    # for simplicity, we assume that the entry block is the first block
    rename_block(blocks['entry'])



def main(program: dict) -> dict:
    blocks = program_to_basic_blocks(program)
    dominators = get_dominators(blocks)
    dominance_frontier = get_dominance_frontier(dominators, blocks)
    globals_, definitions = get_globals(blocks)
    insert_phi_functions(globals_, definitions, dominance_frontier, blocks)
    dom_tree = get_dominance_tree(dominators)
    rename_ssa(blocks, globals_, dom_tree)
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