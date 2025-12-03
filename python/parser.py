# -*- coding: utf-8 -*-


from enum import Enum, auto
from tokenizer import Tokenizer, Tokens


class ParseError(ValueError):
    def __init__(self, lexeme, line, column, expected=None):
        if lexeme is None:
            lexeme = 'EOF'
        if expected is not None:
            msg = (f'Expected {expected} on {line},{column}. ' +
                   f'Instead, got {lexeme}')
        else:
            msg = f'Unexpected symbol -> {lexeme} on {line},{column}'
        super(ValueError, self).__init__(msg)


class Nodes(Enum):
    ARGS = auto()
    CALL = auto()
    BLOCK = auto()
    IF = auto()
    INTEGER = auto()
    OPERATOR = auto()
    PROCEDURE = auto()
    PROGRAM = auto()
    RETURN = auto()
    VAR = auto()
    WHILE = auto()



class Node(object):
    def __init__(self, node_type, line=None,
                 column=None, lexeme=None, nodes=[]):
        self.node_type = node_type
        if line is not None: 
            assert(type(line) is int)
        if column is not None: 
            assert(type(column) is int)
        if lexeme is not None:
            assert(type(lexeme) is str)
        self.line = line
        self.column = column
        self.lexeme = lexeme
        self.nodes = []
        self.add_nodes(*nodes)


    def add_nodes(self, *nodes):
        self.nodes += [node for node in nodes if node is not None]
        return self


    def __str__(self):
        return f'{self.node_type.name} {self.lexeme or ""}'


class Parser(object):
    def __init__(self, source):
        self.tokenizer = Tokenizer(source)
        self._token = None
        self._lexeme = None
        self.last_lexeme = None
        self.last_line = 1
        self.last_column = 1


    def reset(self):
        self.tokenizer.reset()
        self._token = None
        self._lexeme = None
        self.last_lexeme = None
        self.last_line = 1
        self.last_column = 1


    def parse(self):
        root = Node(Nodes.PROGRAM)
        self.token()
        while not self.token_is(None):
            root.add_nodes(self.procedure())
        return root


    def procedure(self):
        name = self.expect(Tokens.IDENTIFIER)
        node = Node(Nodes.PROCEDURE, self.last_line, self.last_column, name) 
        if self.token_is(Tokens.LBRACE):
            node.add_nodes(*self.statement())
        else:
            self.expect(Tokens.LBRACE)
        return node


    def statement(self):
        if self.accept(Tokens.LBRACE):
            statements = []
            while not self.token_is(Tokens.RBRACE):
                res = self.statement()
                if type(res) is list:
                    statements += res
                else:
                    assert(isinstance(res, Node))
                    statements.append(res)
            self.expect(Tokens.RBRACE)
            return statements
        elif self.accept(Tokens.VAR):
            var = self.last_lexeme
            line = self.last_line
            column = self.last_column
            self.expect(Tokens.ASSIGN)
            node = Node(Nodes.OPERATOR, self.last_line, self.last_column, '=',
                        (Node(Nodes.VAR, line, column, var),
                         self.logical_expr()))
            self.expect(Tokens.SEMICOLON)
            return node
        elif self.accept(Tokens.IDENTIFIER):
            proc = self.last_lexeme
            line = self.last_line
            column = self.last_column
            args = []
            if self.accept(Tokens.LPAREN):
                arg = self.logical_expr()
                if arg:
                    args.append(arg)
                while self.accept(Tokens.COMMA):  
                    args.append(self.logical_expr())
                self.expect(Tokens.RPAREN)
            node = Node(Nodes.CALL, line, column, proc, args)
            self.expect(Tokens.SEMICOLON)
            return node
        elif self.accept(Tokens.IF):
            line = self.last_line
            column = self.last_column
            self.expect(Tokens.LPAREN)
            cond = self.logical_expr()
            self.expect(Tokens.RPAREN)
            body = self.statement()
            if isinstance(body, Node):
                body = [body]
            node = Node(Nodes.IF, line, column, None,
                        (cond, Node(Nodes.BLOCK, line, column, None, body)))
            while self.accept(Tokens.ELSE):
                if self.accept(Tokens.IF):
                    line = self.last_line
                    column = self.last_column
                    self.expect(Tokens.LPAREN)
                    cond = self.logical_expr()
                    self.expect(Tokens.RPAREN)
                    body = self.statement()
                    if isinstance(body, Node):
                        body = [body]
                    node.add_nodes(
                        Node(Nodes.IF, line, column, None,
                             (cond, Node(Nodes.BLOCK, line, column, None,
                                         body))))
                else:
                    body = self.statement()
                    if isinstance(body, Node):
                        body = [body]
                    node.add_nodes(Node(Nodes.BLOCK, line, column, None, body))
                    break
            return node
        elif self.accept(Tokens.WHILE):
            line = self.last_line
            column = self.last_column
            self.expect(Tokens.LPAREN)
            cond = self.logical_expr()
            self.expect(Tokens.RPAREN)
            body = self.statement()
            if isinstance(body, Node):
                body = [body]
            return Node(Nodes.WHILE, line, column, None,
                        (cond, Node(Nodes.BLOCK, line, column, None, body)))
        elif self.accept(Tokens.RETURN):
            node = Node(Nodes.RETURN, self.last_line, self.last_column)
            self.expect(Tokens.SEMICOLON)
            return node
        else:
            raise ParseError(self._lexeme,
                             self.tokenizer.line(),
                             self.tokenizer.column())


    def factor(self):
        if self.accept(Tokens.VAR):
            return Node(Nodes.VAR,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme)
        elif self.accept(Tokens.IDENTIFIER):
            node = Node(Nodes.CALL,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme)
            if self.accept(Tokens.LPAREN):
                node.add_nodes(self.logical_expr())
                while self.accept(Tokens.COMMA):
                    node.add_nodes(self.logical_expr())
                self.expect(Tokens.RPAREN)
            return node
        elif self.accept(Tokens.INTEGER):
            return Node(Nodes.INTEGER,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme)
        elif self.accept(Tokens.LPAREN):
            node = self.logical_expr()
            self.expect(Tokens.RPAREN)
            return node
        else:
            raise ParseError(self._lexeme,
                             self.tokenizer.line(),
                             self.tokenizer.column())


    def logical_expr(self):
        node = self.comparative_expr()
        while True:
            if self.accept(Tokens.AND):
                if (node.node_type == Nodes.OPERATOR and
                    node.lexeme == '|'):
                    node.nodes[-1] = Node(Nodes.OPERATOR,
                                          self.last_line, self.last_column, '&'
                                          (node.nodes[-1],
                                           self.comparative_expr()))
                else:
                    node = Node(Nodes.OPERATOR, self.last_line,
                                self.last_column, '&',
                                (node, self.comparative_expr()))
            elif self.accept(Tokens.OR, Tokens.XOR):
                node = Node(Nodes.OPERATOR,
                            self.last_line,
                            self.last_column,
                            self.last_lexeme,
                            (node, self.comparative_expr()))
            else:
                break
        return node


    def comparative_expr(self):
        node = self.arithmetic_expr()
        if self.accept(Tokens.EQUAL, Tokens.NOT_EQUAL,
                       Tokens.GT, Tokens.GT_EQUAL,
                       Tokens.LT, Tokens.LT_EQUAL):
            node = Node(Nodes.OPERATOR,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme,
                        (node, self.arithmetic_expr()))
        return node

    
    def arithmetic_expr(self):
        if self.accept(Tokens.PLUS):
            node = self.term()
        elif self.accept(Tokens.MINUS, Tokens.NOT):
            node = Node(Nodes.OPERATOR,
                        self.last_line,
                        self.last_column,
                        '~' if self.last_lexeme == '-' else '!',
                        (self.term(),))
        else:
            node = self.term()
        while self.accept(Tokens.PLUS, Tokens.MINUS):
            node = Node(Nodes.OPERATOR,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme,
                        (node, self.term(),))
        return node


    def term(self):
        node = self.factor()
        while self.accept(Tokens.MULTIPLY, Tokens.DIVIDE,
                          Tokens.MODULO):
            node = Node(Nodes.OPERATOR,
                        self.last_line,
                        self.last_column,
                        self.last_lexeme,
                        (node, self.factor()))
        return node


    def expect(self, *tokens):
        if not self.accept(*tokens):
            raise ParseError(self._lexeme,
                             self.tokenizer.line(),
                             self.tokenizer.column(),
                             None if len(tokens) > 1 else tokens[0])
        else:
            return self.last_lexeme


    def accept(self, *tokens):
        if self.token_is(*tokens):
            self.token()
            return True
        else:
            return False


    def token(self):
        self.last_lexeme = self._lexeme
        self.last_line = self.tokenizer.line()
        self.last_column = self.tokenizer.column()
        self._token, self._lexeme = self.tokenizer.token()
        while self.token_is(Tokens.COMMENT):
            self._token, self._lexeme = self.tokenizer.token()


    def token_is(self, *tokens):
        return self._token in tokens



if __name__ == '__main__':
    import sys


    def print_tree(node, l=0):
        print(f'{".  "*l}{node}')
        [print_tree(child, l+1) for child in node.nodes]


    try:
        with open(sys.argv[1], 'rt') as f:
            parser = Parser(f.read())
    except:
        print(f'Usage: {sys.executable} {sys.argv[0]} <Source File>')
    else:
        try:
            root = parser.parse()
            print_tree(root)
            print()
            print('File successfully parsed.')
        except ParseError:
            import traceback
            traceback.print_exc()

