import sys
import json
from typing import Tuple


def del_list_indexes(l, id_to_del):
    somelist = [i for j, i in enumerate(l) if j not in id_to_del]
    return somelist



def remove_unused_vars(program: dict) -> Tuple[bool,dict]:
    assigned_vars = set()
    used_vars = set()
    changed = False
    for function in program['functions']:
        for instr in function['instrs']:
            if 'dest' in instr:
                dest = instr['dest']
                assigned_vars.add(dest)

            if 'args' in instr:
                for arg in instr['args']:
                    used_vars.add(arg)

        unused_vars = set()
        for assigned_var in assigned_vars:
            if assigned_var not in used_vars:
                unused_vars.add(assigned_var)


    for unused_var in unused_vars:
        for function in program['functions']:
            for idx,instr in enumerate(function['instrs']):
                if 'dest' in instr:
                    dest = instr['dest']
                    if dest == unused_var:
                        changed = True
                        function['instrs'].pop(idx)
                        break

    return changed,program


def remove_unused_assignments(program: dict) -> Tuple[bool,dict]:
    assigned_vars = set()
    used_vars = set()
    to_remove = []
    changed = False
    for function in program['functions']:
        for idx,instr in enumerate(function['instrs']):
            if 'dest' in instr:
                dest = instr['dest']
                for assigned_var in assigned_vars:
                    if assigned_var[0] == dest and dest not in used_vars:
                        prev_assign_index = assigned_var[1]
                        to_remove.append(prev_assign_index)
                        break

                assigned_vars.add((dest,idx))




            if 'args' in instr:
                for arg in instr['args']:
                    used_vars.add(arg)

    changed = len(to_remove) > 0

    for function in program['functions']:
        function['instrs'] = del_list_indexes(function['instrs'], to_remove)

    return changed,program


def delete_block(function: dict, start: int) -> Tuple[bool,dict]:
    changed = False

    for idx,instr in enumerate(function[start+1:], start=start+1):
        if 'label' in instr:
            break

        changed = True


    del function[start+1:idx]
    return changed, function


def remove_dead_branch(program: dict) -> Tuple[bool,dict]:
    changed = False
    for function in program['functions']:
        for instr in function['instrs']:
            if 'op' in instr and instr['op'] == 'br':
                condition = instr['args'][0]
                false_label, true_label = instr['labels']
                const_condition_value = None
                for instr in function['instrs']:
                    if instr['op'] == 'const' and instr['dest'] == condition:
                        const_condition_value = instr['value']
                        break

                if const_condition_value is not None:
                    for idx,instr in enumerate(function['instrs']):
                        if 'label' in instr:
                            delete_block_cond = (instr['label'] == true_label and const_condition_value is False) or (
                                instr['label'] == false_label and const_condition_value is True)
                            if delete_block_cond:
                                changed, _ = delete_block(function['instrs'], idx)
                                break

    return changed,program

def remove_code_after_terminator(program: dict) -> Tuple[bool,dict]:
    changed = False
    for function in program['functions']:
        for idx,instr in enumerate(function['instrs']):
            if 'op' in instr and instr['op'] in ['jmp', 'ret']:
                changed, _ = delete_block(function['instrs'], idx)
                break

    return changed,program




def main(program: dict) -> dict:
    changed = True
    while changed:
        removed_unused_var, program = remove_unused_vars(program)
        removed_dead_branch, program = remove_dead_branch(program)
        removed_unused_assignment, program = remove_unused_assignments(program)
        removed_code_after_terminator, program = remove_code_after_terminator(program)
        changed = removed_unused_var or removed_unused_assignment or removed_dead_branch or removed_code_after_terminator

    return program



if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            program = json.load(f)
    else:
        program = sys.stdin.read()
        program = json.loads(program)

    dce_program = main(program)
    print(json.dumps(dce_program))