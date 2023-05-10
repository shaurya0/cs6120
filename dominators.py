import sys
import json
from typing import Tuple, List, Dict, Set
from typing_extensions import TypeAlias
from dataclasses import dataclass
from ordered_set import OrderedSet
import random
random.seed(0)


_DEFAULT_LABEL = 'entry'

@dataclass
class BasicBlock:
    label: str
    instrs: List[dict]
    predecessors: OrderedSet[str]
    successors: OrderedSet[str]


def program_to_basic_blocks(program: dict) -> Dict[str, BasicBlock]:
    basic_blocks = {}
    predecessors = {}


    for function in program['functions']:
        assert len(function['instrs']) > 0
        label = _DEFAULT_LABEL
        first_instr = function['instrs'][0]
        if 'label' not in first_instr:
            function['instrs'].insert(0, {'label': label})

        instrs = []
        blocks = []
        for instr in function['instrs']:
            if 'label' in instr and len(instrs) > 0:
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
            label, instrs, OrderedSet(predecessors[label]), OrderedSet(successors))


    for label, block in basic_blocks.items():
        block.predecessors =  block.predecessors.union(set(predecessors[label]))
    return basic_blocks


def get_dominators(basic_blocks: Dict[str, BasicBlock]) -> Dict[str, OrderedSet[str]]:
    dominators = {}
    for label, block in basic_blocks.items():
        dominators[label] = set(basic_blocks.keys())


    dominators[_DEFAULT_LABEL] = OrderedSet([_DEFAULT_LABEL])

    changed = True
    while changed:
        changed = False
        for label, block in basic_blocks.items():
            if label == _DEFAULT_LABEL:
                continue


            vertex_preds = OrderedSet()
            if len(block.predecessors) > 0:
                predecessors = list(block.predecessors)
                vertex_preds |= dominators[predecessors[0]]
                for pred in predecessors[1:]:
                    vertex_preds &= dominators[pred]

            vertex_preds.add(label)
            new_dominators = vertex_preds

            if new_dominators != dominators[label]:
                changed = True
                dominators[label] = new_dominators

    return dominators


def get_dominance_tree(dominators) -> Dict[str, List[str]]:
    dom_tree = {k : [] for k in dominators.keys()}
    for node, dom in dominators.items():
        tmp = dom.copy()
        tmp.remove(node)
        if len(tmp) > 0:
            dom_tree[tmp[-1]].append(node)

    return dom_tree


def get_dominance_frontier(dominators: Dict[str, OrderedSet[str]], basic_blocks: Dict[str, BasicBlock]):
    dominance_frontier = {k: [] for k in dominators.keys()}
    for node, block in basic_blocks.items():
        predecessors = basic_blocks[node].predecessors

        if len(predecessors) >= 2:
            imm_dom = dominators[node][-2]
            for pred in predecessors:
                runner = pred
                while runner != imm_dom:
                    dominance_frontier[runner].append(node)
                    runner = dominators[runner][-2]

    return dominance_frontier






def main(program: dict) -> dict:
    basic_blocks = program_to_basic_blocks(program)
    dominators = get_dominators(basic_blocks)
    dominance_tree = get_dominance_tree(dominators)
    dominance_frontier = get_dominance_frontier(dominators, basic_blocks)
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