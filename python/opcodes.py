# -*- coding: utf-8 -*-


from enum import IntEnum


class Opcodes(IntEnum):
    JMP = 0x7f5a
    EOC = 0x7f5b
    NOT = 0x7f5c
    JIZ = 0x7f5e
    NEG = 0x7f5d
    ASS = 0x7f5f
    ADD = 0x7f60
    SUB = 0x7f61
    MUL = 0x7f62
    DIV = 0x7f63
    MOD = 0x7f64
    EQ = 0x7f65
    NEQ = 0x7f66
    GT = 0x7f67
    LT = 0x7f68
    GTE = 0x7f69
    LTE = 0x7f6a
    AND = 0x7f6b
    OR = 0x7f6c
    XOR = 0x7f6d

    # To be added:
    INC = 0x7f6e   #Increment opcode
    DEC = 0x7f6f   #Decrement opcode
    SLEEP = 0x7f70 #Opcode for overloaded function sleep
    SKIP = 0x7f71   #None-opcode

    AIM = 0x7f77
    CHAN = 0x7f78
    MISS = 0x7f79
    NUKE = 0x7f7a
    SHLD = 0x7f7b
    SPX = 0x7f7c
    SPY = 0x7f7d
    SIG = 0x7f7e
    ARCT = 0x7f7f
    SQRT = 0x7f80
    COL = 0x7f81
    DMG = 0x7f82
    EGY = 0x7f83
    RDR = 0x7f84
    RND = 0x7f85
    RNGE = 0x7f86
    XPOS = 0x7f87
    YPOS = 0x7f88
    FIRE = 0x7f89
    MOVX = 0x7f8a
    MOVY = 0x7f8b

    A = 0x7f95
    B = 0x7f96
    C = 0x7f97
    D = 0x7f98
    E = 0x7f99
    F = 0x7f9a
    G = 0x7f9b
    H = 0x7f9c
    I = 0x7f9d
    J = 0x7f9e
    K = 0x7f9f
    L = 0x7fa0
    M = 0x7fa1
    N = 0x7fa2
    O = 0x7fa3
    P = 0x7fa4
    Q = 0x7fa5
    R = 0x7fa6
    S = 0x7fa7
    T = 0x7fa8
    U = 0x7fa9
    V = 0x7faa
    W = 0x7fab
    X = 0x7fac
    Y = 0x7fad
    Z = 0x7fae

    @staticmethod
    def is_special(inst):
        return inst in SPECIAL_VARS

    @staticmethod
    def is_function(inst):
        return inst in FUNCTIONS

    @staticmethod
    def nargs(inst):
        try:
            if Opcodes.is_special(inst):
                return 1 if Opcodes.is_procedure(inst) else 0
            else:
                return (1 if Opcodes.is_procedure(inst)
                        else FUNCTIONS[inst])
        except KeyError:
            return 0

    @staticmethod
    def is_procedure(inst):
        return inst in PROCEDURES

    @staticmethod
    def is_var(inst):
        return inst >= Opcodes.A and inst <= Opcodes.Z

    @staticmethod
    def is_unary(inst):
        return inst in UNARY

    @staticmethod
    def is_binary(inst):
        return inst in BINARY

    @staticmethod
    def is_jump(inst):
        return inst in JUMPS

    @classmethod
    def name_of(cls, inst):
        try:
            return cls(inst).name
        except ValueError:
            return 'UNK'


BINARY = (
    Opcodes.ADD,
    Opcodes.SUB,
    Opcodes.MUL,
    Opcodes.DIV,
    Opcodes.MOD,
    Opcodes.EQ,
    Opcodes.NEQ,
    Opcodes.GT,
    Opcodes.LT,
    Opcodes.GTE,
    Opcodes.LTE,
    Opcodes.AND,
    Opcodes.OR,
    Opcodes.XOR,
)

UNARY = (
    Opcodes.NOT,
    Opcodes.NEG,
)

JUMPS = (
    Opcodes.JMP,
    Opcodes.JIZ,
)

SPECIAL_VARS = (
    Opcodes.AIM,
    Opcodes.CHAN,
    Opcodes.MISS,
    Opcodes.NUKE,
    Opcodes.SHLD,
    Opcodes.SIG,
    Opcodes.SPX,
    Opcodes.SPY,
    Opcodes.COL,
    Opcodes.DMG,
    Opcodes.EGY,
    Opcodes.RDR,
    Opcodes.RNGE,
    Opcodes.XPOS,
    Opcodes.YPOS,
    Opcodes.RND,
)

FUNCTIONS = {
    Opcodes.ARCT: 2,
    Opcodes.RND: 0,
    Opcodes.SQRT: 1,
}

PROCEDURES = (
    Opcodes.AIM,
    Opcodes.CHAN,
    Opcodes.FIRE,
    Opcodes.MISS,
    Opcodes.NUKE,
    Opcodes.SHLD,
    Opcodes.SIG,
    Opcodes.SPX,
    Opcodes.SPY,
    Opcodes.MOVX,
    Opcodes.MOVY,
)

