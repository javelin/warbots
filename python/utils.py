# -*- coding: utf-8 -*-

import struct

from opcodes import Opcodes


OFFS_HEADER = 0    #Size: 8
OFFS_NAME = 8      #Size: 20


# Attributes
OFFS_ENERGY = 36   #0, 1, 2, 3
OFFS_SHIELD = 38   #0, 1, 2, 3
OFFS_ARMOR = 40    #0, 1, 2, 3
OFFS_SPEED = 42    #0, 1, 2, 3
OFFS_BULLET = 44   #0, 1, 2
OFFS_MISSILES = 46 #bool
OFFS_TACNUKES = 47 #bool

OFFS_ICON1 = 48    #Size: 1024
OFFS_ICON2 = 1072  #Size: 1024

OFFS_IS_COMPILED = 2096   #bool
OFFS_BYTECODE_SIZE = 2100 #short
OFFS_BYTECODE = 2102

OFFS_CODE_START = 2104

SHORT_SIZE = 2
ATTRIB_SIZE = SHORT_SIZE
BOOL_SIZE = 1
HEADER_SIZE = 8
NAME_SIZE = 20
ICON_SIZE = 1024


def is_int(n):
    return n >= -32000 and n <= 32000


def inst2str(inst):
    if is_int(inst):
        return f'{inst}'
    else:
        return Opcodes.name_of(inst)


def str2inst(m):
    try:
        return Opcodes.__members__[m]
    except KeyError:
        try:
            return int(m)
        except ValueError:
            return Opcodes.SKIP


def prettify(b):
    def inst(i, c):
        s = '%02d %04x' % (i, c)
        s += f' {c}' if c < 0x7f00 else f' {inst2str(c)}'
        return s
    return '\n'.join([inst(i, struct.unpack_from('<H', b[2:], i*2)[0])
                      for i in range(len(b) // 2 - 1)])

def prettify_code(b):
    def _inst(i, c):
        s = '%02d %04x' % (i, c)
        s += f' {c}' if c < 0x7f00 else f' {inst2str(c)}'
        return s
    
    def inst(i, c):
        try:
            return _inst(i, int(c))
        except:
            return '%02d %s' % (i, c)
    
    return '\n'.join([inst(i, c) for i, c in enumerate(b)])

