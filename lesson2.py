import json
import numpy as np

def main():
    add_json = r'bril\test\parse\add.json'
    with open(add_json, 'r') as fid:
        program = json.load(fid)
        num_adds = 0
        for instr in program['functions'][0]['instrs']:
            if instr['op'] == 'add':
                num_adds += 1

        print('Number of adds: {}'.format(num_adds))










if __name__ == '__main__':
    main()