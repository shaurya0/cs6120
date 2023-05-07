import sys
import json
from typing import Tuple, List, Dict, Set
from typing_extensions import TypeAlias
from dataclasses import dataclass
import random
random.seed(0)

@dataclass
class BasicBlock:
    label: str
    instrs: List[dict]
    predecessors: Set[str]
    successors: Set[str]



def program_to_basic_blocks(program: dict) -> Dict[str, BasicBlock]:
    basic_blocks = {}
    predecessors = {}

    for function in program['functions']:
        label = 'b1'
        instrs = []
        blocks = []
        for instr in function['instrs']:
            if 'label' in instr:
                blocks.append((label,instrs))
                predecessors[label] = []
                label = instr['label']
                instrs = []


            # if 'dest' in instr:
                # instr['dest'] = instr['dest'] + '.' + label
            instrs.append(instr)

        blocks.append((label, instrs))
        predecessors[label] = []

    for i, (label, instrs) in enumerate(blocks):
        successors = []
        branch_found = False
        for instr in instrs:
            if 'op' in instr and instr['op'] in ['jmp', 'br']:
                branch_found = True
                for l in instr['labels']:
                    successors.append(l)
                    predecessors[l].append(label)

        # yikes
        if len(predecessors[label]) == 0 and i > 0:
            prev_label = blocks[i-1][0]
            predecessors[label] = [prev_label]

        # double yikes
        if not branch_found and i  == 0:
            next_label = blocks[i+1][0]
            successors.append(next_label)

        basic_blocks[label] = BasicBlock(
            label, instrs, set(predecessors[label]), set(successors))


    for label, block in basic_blocks.items():
        block.predecessors =  block.predecessors.union(set(predecessors[label]))
    return basic_blocks


def data_flow_worklist(blocks: Dict[str, BasicBlock], merge_fn, transfer_fn):
    in_ = {}
    out = {}
    for label in blocks.keys():
        in_[label] = {}
        out[label] = {}


    worklist = []
    for block in blocks.values():
        worklist.append(block)

    while len(worklist) > 0:
        block = worklist.pop(0)
        label = block.label
        out_prev = out[label].copy()
        in_[label] = merge_fn([out[p] for p in block.predecessors])
        out[label] = transfer_fn(block, in_[label])

        if out_prev != out[label]:
            for l in block.successors:
                found = False
                for b in worklist:
                    if b.label == l:
                        found = True
                        break
                if not found:
                    worklist.extend([v for ll,v in blocks.items() if ll == l])



    return in_, out


def reaching_definition(blocks: Dict[str, BasicBlock]):
    def merge_fn(out_prev: List[Set[str]]):
        result = set()
        for o in out_prev:
            result = result.union(o)
        return result

    def transfer_fn(block, in_):
        result = set()
        for instr in block.instrs:
            if 'dest' in instr:
                result.add(instr['dest'])

        result = result.union(in_)
        return result

    return data_flow_worklist(blocks, merge_fn, transfer_fn)


def main(program: dict) -> dict:
    basic_blocks = program_to_basic_blocks(program)

    in_, out = reaching_definition(basic_blocks)
    for l, v in in_.items():
        in_defs = v
        out_defs = out[l]
        print(f'{l}:')
        in_defs_str = ', '.join(sorted(in_defs))
        out_defs_str = ', '.join(sorted(out_defs))
        if in_defs_str == '':
            in_defs_str = '∅'


        print(f'  in:  {in_defs_str}')
        print(f'  out: {out_defs_str}')




    return program



if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            program = json.load(f)
    else:
        program = sys.stdin.read()
        program = json.loads(program)

    program = main(program)
    # print(json.dumps(program))