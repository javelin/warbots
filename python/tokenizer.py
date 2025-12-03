# -*- coding: utf-8 -*-

from enum import Enum, auto


class Tokens(Enum):
    AND = auto()
    ASSIGN = auto()
    COMMA = auto()
    COMMENT = auto()
    DIVIDE = auto()
    ELSE = auto()
    EQUAL = auto()
    GT = auto()
    GT_EQUAL = auto()
    IDENTIFIER = auto()
    IF = auto()
    INTEGER = auto()
    LBRACE = auto()
    LPAREN = auto()
    LT = auto()
    LT_EQUAL = auto()
    MINUS = auto()
    MODULO = auto()
    MULTIPLY = auto()
    NOT = auto()
    NOT_EQUAL = auto()
    OR = auto()
    PLUS = auto()
    RBRACE = auto()
    RETURN = auto()
    RPAREN = auto()
    SEMICOLON = auto()
    UNKNOWN = auto()
    VAR = auto()
    WHILE = auto()
    XOR = auto()


class States(Enum):
    START = auto()
    IN_BANG = auto()
    IN_COMMENT = auto()
    IN_EQUAL = auto()
    IN_GT = auto()
    IN_IDENT = auto()
    IN_INT = auto()
    IN_LINE_COMMENT = auto()
    IN_LT = auto()
    IN_SLASH = auto()


class Tokenizer(object):
    reserved = {
        ',': Tokens.COMMA,
        '{': Tokens.LBRACE,
        '}': Tokens.RBRACE,
        '(': Tokens.LPAREN,
        ')': Tokens.RPAREN,
        '+': Tokens.PLUS,
        '-': Tokens.MINUS,
        '*': Tokens.MULTIPLY,
        '/': Tokens.DIVIDE,
        '!': Tokens.NOT,
        '&': Tokens.AND,
        '|': Tokens.OR,
        '^': Tokens.XOR,
        ';': Tokens.SEMICOLON,
        'else': Tokens.ELSE,
        'if': Tokens.IF,
        'return': Tokens.RETURN,
        'while': Tokens.WHILE,
    }

    def __init__(self, source):
        self.ptr = 0
        self._line = 1
        self._column = 0
        self.start_line = None
        self.start_column = None
        self.source = source.replace('\r\n', '\n').replace('\r', '\n')
        self.state = States.START

    def reset(self):
        self.ptr = 0
        self._line = 1
        self._column = 0
        self.start_line = None
        self.start_column = None
        self.state = States.START

    def token(self):
        lastc = None
        lexeme = ''
        state = States.START
        self.start_line = None
        self.start_column = None
        while True:
            c = self.get()
            if state == States.START:
                self.start_line = self._line
                self.start_column = self._column
                if c is None:
                    return None, None
                elif c.isspace():
                    continue
                elif c == '!':
                    state = States.IN_BANG
                elif c.isidentifier():
                    state = States.IN_IDENT
                elif c.isdigit():
                    state = States.IN_INT
                elif c == '/':
                    state = States.IN_SLASH
                elif c == '>':
                    state = States.IN_GT
                elif c == '<':
                    state = States.IN_LT
                elif c == '=':
                    state = States.IN_EQUAL
                elif c in self.reserved:
                    return self.reserved[c], c
                else:
                    return Tokens.UNKNOWN, c
            elif state == States.IN_BANG:
                if c == '=':
                    return Tokens.NOT_EQUAL
                else:
                    self.unget()
                    return Tokens.NOT, lexeme
            elif state == States.IN_COMMENT:
                if c == '/':
                    if lastc == '*':
                        return Tokens.COMMENT, lexeme
            elif state == States.IN_EQUAL:
                if c == '=':
                    return Tokens.EQUAL, lexeme + c
                else:
                    self.unget()
                    return Tokens.ASSIGN, lexeme
            elif state == States.IN_GT:
                if c == '=':
                    return Tokens.GT_EQUAL, lexeme + c
                else:
                    self.unget()
                    return Tokens.GT, lexeme
            elif state == States.IN_IDENT:
                if (c is not None and not c.isdigit() and
                    not c.isidentifier()):
                    self.unget()
                    try:
                        return self.reserved[lexeme.lower()], lexeme
                    except:
                        if lexeme.lower() in list(
                                'abcdefghijklmnopqrstuvwxyz'):
                            return Tokens.VAR, lexeme
                        else:
                            return Tokens.IDENTIFIER, lexeme
            elif state == States.IN_INT:
                if c is not None and not c.isdigit():
                    self.unget()
                    return Tokens.INTEGER, lexeme
            elif state == States.IN_LINE_COMMENT:
                if c in ('\n', None):
                    return Tokens.COMMENT, lexeme
            elif state == States.IN_LT:
                if c == '=':
                    return Tokens.LT_EQUAL, lexeme + c
                else:
                    self.unget()
                    return Tokens.LT, lexeme
            elif state == States.IN_SLASH:
                if c == '/':
                    state = States.IN_LINE_COMMENT
                elif c == '*':
                    state = States.IN_COMMENT
                else:
                    self.unget()
                    return Tokens.DIVIDE, lexeme

            lexeme += c
            lastc = c
            
    def get(self):
        try:
            advance_line = self.ptr > 1 and self.source[self.ptr - 1] == '\n'
            c = self.source[self.ptr]
            self.ptr += 1
            self._column += 1
            if advance_line:
                self._line += 1
                self._column = 1
            return c
        except:
            return None

    def unget(self):
        if self.ptr < len(self.source) and self.ptr > 0:
            self.ptr -= 1
            self._column -= 1
            if self.source[self.ptr] == '\n' and self._line > 1:
                self._line -= 1
                newline_pos = self.source.rfind('\n', 0, self.ptr)
                self._column = self.ptr - max(newline_pos, 0)

    def line(self):
        return self.start_line

    def column(self):
        return self.start_column



if __name__ == '__main__':
    import sys
    try:
        with open(sys.argv[1], 'rt') as f:
            scode = f.read()
            t = Tokenizer(scode)
            while True:
                token, lexeme = t.token()
                if token is None:
                    break
                else:
                    print(token.name, lexeme, f'{t.column()}, {t.line()}')
    except:
        import traceback
        traceback.print_exc()
