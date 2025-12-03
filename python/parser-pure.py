# -*- coding: utf-8 -*-


from enum import Enum, auto
from tokenizer import Tokenizer, Tokens


class ParseError(ValueError):
    def __init__(self, lexeme, line, expected=None):
        if lexeme is None:
            lexeme = 'EOF'
        if expected is not None:
            msg = f'Expected {expected} on line {line}, instead, got {lexeme}'
        else:
            msg = f'Unexpected symbol -> {lexeme} on line {line}'
        super(ValueError, self).__init__(msg)


class Parser(object):
    def __init__(self, source):
        self.tokenizer = Tokenizer(source)
        self._token = None
        self._lexeme = None


    def reset(self):
        self.tokenizer.reset()
        self._token = None
        self._lexeme = None
        self.last_lexeme = None


    def parse(self):
        self.token()
        self.procedure()
        while not self.token_is(None):
            self.procedure()


    def procedure(self):
        self.expect(Tokens.IDENTIFIER)
        self.expect(Tokens.LBRACE)
        while not self.token_is(Tokens.RBRACE):
            self.statement()
        self.expect(Tokens.RBRACE)


    def statement(self):
        if self.accept(Tokens.LBRACE):
            while not self.token_is(Tokens.RBRACE):
                self.statement()
            self.expect(Tokens.RBRACE)
        elif self.accept(Tokens.VAR):
            self.expect(Tokens.ASSIGN)
            self.logical_expr()
            self.expect(Tokens.SEMICOLON)
        elif self.accept(Tokens.IDENTIFIER):
            if self.accept(Tokens.LPAREN):
                self.logical_expr()
                self.expect(Tokens.RPAREN)
            self.expect(Tokens.SEMICOLON)
        elif self.accept(Tokens.IF):
            self.expect(Tokens.LPAREN)
            self.logical_expr()
            self.expect(Tokens.RPAREN)
            self.statement()
            while self.accept(Tokens.ELSE):
                if self.accept(Tokens.IF):
                    self.expect(Tokens.LPAREN)
                    self.logical_expr()
                    self.expect(Tokens.RPAREN)
                    self.statement()
                else:
                    self.statement()
                    break
        elif self.accept(Tokens.WHILE):
            self.expect(Tokens.LPAREN)
            self.logical_expr()
            self.expect(Tokens.RPAREN)
            self.statement()
        elif self.accept(Tokens.RETURN):
            self.expect(Tokens.SEMICOLON)
        else:
            raise ParseError(self._lexeme, self.tokenizer.line)


    def factor(self):
        if self.accept(Tokens.VAR):
            pass
        elif self.accept(Tokens.IDENTIFIER):
            if self.accept(Tokens.LPAREN):
                self.logical_expr()
                self.expect(Tokens.RPAREN)
        elif self.accept(Tokens.INTEGER):
            pass
        elif self.accept(Tokens.LPAREN):
            self.logical_expr()
            self.expect(Tokens.RPAREN)
        else:
            raise ParseError(self._lexeme, self.tokenizer.line)


    def logical_expr(self):
        self.comparative_expr()
        while self.accept(Tokens.AND, Tokens.OR, Tokens.XOR):
            self.comparative_expr()


    def comparative_expr(self):
        self.arithmetic_expr()
        if self.accept(Tokens.EQUAL, Tokens.NOT_EQUAL,
                       Tokens.GT, Tokens.GT_EQUAL,
                       Tokens.LT, Tokens.LT_EQUAL):
            self.arithmetic_expr()
            

    def arithmetic_expr(self):
        if self.accept(Tokens.PLUS, Tokens.MINUS, Tokens.NOT):
            pass

        self.term()
        while self.accept(Tokens.PLUS, Tokens.MINUS):
            self.term()


    def term(self):
        self.factor()
        while self.accept(Tokens.MULTIPLY, Tokens.DIVIDE, Tokens.MODULO):
            self.factor()


    def expect(self, *tokens):
        if not self.accept(*tokens):
            raise ParseError(_lexeme, self.tokenizer.line,
                             None if len(tokens) > 1 else tokens[0])


    def accept(self, *tokens):
        if self.token_is(*tokens):
            self.token()
            return True
        else:
            return False


    def token(self):
        self.last_lexeme = self._lexeme
        self._token, self._lexeme = self.tokenizer.token()
        while self.token_is(Tokens.COMMENT):
            self._token, self._lexeme = self.tokenizer.token()


    def token_is(self, *tokens):
        return self._token in tokens



if __name__ == '__main__':
    import sys
    try:
        with open(sys.argv[1], 'rt') as f:
            parser = Parser(f.read())
    except:
        print(f'Usage: {sys.executable} {sys.argv[0]} <Source File>')
    else:
        try:
            parser.parse()
            print('File successfully parsed.')
        except ParseError:
            import traceback
            traceback.print_exc()
