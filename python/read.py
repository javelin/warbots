# -*- coding: utf-8 -*-

import argparse
import struct

import attribs
import opcodes

class HeaderError(Exception): pass

OFFS_HEADER = 0
OFFS_NAME = 8

OFFS_CODE = 28

OFFS_ENERGY = 36 #0, 1, 2, 3
OFFS_SHIELD = 38 #0, 1, 2, 3
OFFS_ARMOR = 40 #0, 1, 2, 3
OFFS_SPEED = 42 #0, 1, 2, 3
OFFS_BULLET = 44 #0, 1, 2
OFFS_MISSILES = 46 #bool
OFFS_TACNUKES = 47 #bool

OFFS_ICON1 = 48
OFFS_ICON2 = 1072
OFFS_COMPILED = 2096
OFFS_BYTECODE_SIZE = 2100
OFFS_BYTECODE = 2102

OFFS_SOC = 2104 #Start of code; push EOC address to stack??

def conv(b):
    def opname(c):
        try:
            return opcodes.NAMES[c]
        except:
            return 'UNKOWNXX'
    def line(i, c):
        s = '%02d %04x' % (i, c)
        s += f' {c}' if c < 0x7f00 else f' {opname(c)}'
        return s
    print('\n'.join([line(i, struct.unpack_from('<H', b[2:], i*2)[0])
                    for i in range(len(b) // 2 - 1)]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('WB Save File', type=str)
    args = parser.parse_args()
    fn = getattr(args, 'WB Save File')
    with open(fn, 'rb') as f:
        buff = f.read()
        print(len(buff))
        header, = struct.unpack_from('8s', buff, OFFS_HEADER)
        if header != b'WBMD2.0\x00':
            raise HeaderError()
        name, = struct.unpack_from('20s', buff, OFFS_NAME)
        print('Name:', name.decode('ascii'))

        print('Energy: ',
              attribs.LEVEL_NAMES[struct.unpack_from('<H', buff,
                                                     OFFS_ENERGY)[0]])
        print('Shield: ',
              attribs.LEVEL_NAMES[struct.unpack_from('<H', buff,
                                                     OFFS_SHIELD)[0]])
        print('Armor: ',
              attribs.STRENGTH_NAMES[struct.unpack_from(
                  '<H', buff, OFFS_ARMOR)[0]])
        print('CPU Speed: ',
              attribs.CPC_VALUES[struct.unpack_from('<H', buff,
                                                    OFFS_SPEED)[0]],
              'cpc')
        print('Bullet: ',
              attribs.BULLET_NAMES[struct.unpack_from(
                  '<H', buff, OFFS_BULLET)[0]])
        print('Missiles: ',
              'Yes' if struct.unpack_from('?', buff, OFFS_MISSILES)[0]
              else 'No')
        print('Tactical Nukes: ',
              'Yes' if struct.unpack_from('?', buff, OFFS_TACNUKES)[0]
              else 'No')

        #attribs, = struct.unpack_from('9s', buff, OFFS_CODE)
        #print(attribs)
        #print(len(attribs))
        

        #attribs, = struct.unpack_from('20s', buff, OFFS_CODE)
        #print(attribs)
        #print(len(attribs))
        temp, = struct.unpack_from(f'{OFFS_ENERGY - OFFS_CODE}s',
                                   buff, OFFS_CODE)
        print('Unknown1:', temp)

        temp, = struct.unpack_from(
            f'{OFFS_BYTECODE_SIZE - OFFS_COMPILED}s',
            buff, OFFS_COMPILED)
        print('Unknown2:', temp)
        
        icon1, = struct.unpack_from('1024s', buff, OFFS_ICON1)
        icon2, = struct.unpack_from('1024s', buff, OFFS_ICON2)
        is_compiled, = struct.unpack_from('?', buff, OFFS_COMPILED)
        print(f'Code is {"" if is_compiled else "un"}compiled.')
        size, = struct.unpack_from('<H', buff, OFFS_BYTECODE_SIZE)
        bytecode, = struct.unpack_from(f'{size*2}s',
                                       buff, OFFS_BYTECODE)
        print('Size when compiled:', size if is_compiled else 'N/A')
        print('Compiled code:', bytecode if is_compiled else 'N/A')
        usize = len(buff) - (OFFS_BYTECODE_SIZE + 2 + (size*2)) - 2
        print(f'Uncompiled source code (Size: {usize})\n',
              buff[-usize:].decode('ascii'))

        if is_compiled:
            print()
            print(bytecode)
            conv(bytecode)
