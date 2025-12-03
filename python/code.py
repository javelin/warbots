# -*- coding: utf-8 -*-

import re

from opcodes import Opcodes
from versions import Versions
try:
    from parser import Nodes
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(os.getcwd()))
    from wb.parser import Nodes


class CodeError(Exception): pass


class CodeGenerator(object):
    CALL_MAP = {
        'aim': Opcodes.AIM,
        'channel': Opcodes.CHAN,
        'missile': Opcodes.MISS,
        'nuke': Opcodes.NUKE,
        'shield': Opcodes.SHLD,
        'speedx': Opcodes.SPX,
        'speedy': Opcodes.SPY,
        'signal': Opcodes.SIG,
        'arctan': Opcodes.ARCT,
        'sqrt': Opcodes.SQRT,
        'collision': Opcodes.COL,
        'damage': Opcodes.DMG,
        'energy': Opcodes.EGY,
        'radar': Opcodes.RDR,
        'random': Opcodes.RND,
        'range': Opcodes.RNGE,
        'xpos': Opcodes.XPOS,
        'ypos': Opcodes.YPOS,
        'fire': Opcodes.FIRE,
        'movex': Opcodes.MOVX,
        'movey': Opcodes.MOVY,
    }

    CALL_ARGS = {
        Opcodes.AIM: 1,
        Opcodes.CHAN: 1,
        Opcodes.MISS: 1,
        Opcodes.NUKE: 1,
        Opcodes.SHLD: 1,
        Opcodes.SPX: 1,
        Opcodes.SPY: 1,
        Opcodes.SIG: 1,
        Opcodes.ARCT: 2,
        Opcodes.SQRT: 1,
        Opcodes.COL: 0,
        Opcodes.DMG: 0,
        Opcodes.EGY: 0,
        Opcodes.RDR: 0,
        Opcodes.RND: 0,
        Opcodes.RNGE: 0,
        Opcodes.XPOS: 0,
        Opcodes.YPOS: 0,
        Opcodes.FIRE: 1,
        Opcodes.MOVX: 1,
        Opcodes.MOVY: 1,
    }

    OVERLOADED = (
        Opcodes.AIM,
        Opcodes.CHAN,
        Opcodes.MISS,
        Opcodes.NUKE,
        Opcodes.SHLD,
        Opcodes.SPX,
        Opcodes.SPY,
        Opcodes.SIG,
        Opcodes.MOVX,
        Opcodes.MOVY,
    )

    OPERATOR_MAP = {
        '!': Opcodes.NOT,
        '~': Opcodes.NEG,
        '=': Opcodes.ASS,
        '+': Opcodes.ADD,
        '-': Opcodes.SUB,
        '*': Opcodes.MUL,
        '/': Opcodes.DIV,
        '%': Opcodes.MOD,
        '==': Opcodes.EQ,
        '!=': Opcodes.NEQ,
        '>': Opcodes.GT,
        '<': Opcodes.LT,
        '>=': Opcodes.GTE,
        '<=': Opcodes.LTE,
        '&': Opcodes.AND,
        '|': Opcodes.OR,
        '^': Opcodes.XOR,
    }

    def __init__(self, syntax_tree, version=Versions.V2_0_0):
        self.syntax_tree = syntax_tree
        self.version = version
        self.symtab = {}
        self.code = []
        self.statement_handlers = {
            Nodes.CALL: self.handle_call,
            Nodes.IF: self.handle_if,
            Nodes.OPERATOR: self.handle_operator,
            Nodes.RETURN: self.handle_return,
            Nodes.WHILE: self.handle_while,
        }
 

    def reset(self):
        self.symtab = {}
        self.code = []


    def generate(self):
        self.reset()
        main = [node for node in self.syntax_tree.nodes
                if node.lexeme.lower() == 'main']
        if not main: 
            raise CodeError("Unable to find 'main' procedure")
        
        self.code = [0, 'CALL_main', Opcodes.JMP] #1

        init = [node for node in self.syntax_tree.nodes
                if node.lexeme.lower() == 'init']
        if init:
            self.code[0] = 3 #2
            self.code = [3, 'CALL_init', Opcodes.JMP] + self.code #2
            
            ## Optimization: there is no JMP from init to main.
            self.procedure(init[0], return_jump=False)

        self.procedure(main[0])

        ## Generate code for the rest of the procedures
        [self.procedure(node) for node in self.syntax_tree.nodes
            if node.lexeme.lower() not in ('init', 'main')]

        ## Fill the call addresses
        for addr in range(len(self.code)):
            found = re.findall(r'^CALL_(.+)', str(self.code[addr]))
            if found:
                self.code[addr] = self.symtab[found[0]]

        ## Add the End-of-code opcode for completeness
        ## (And compatibility with lower versions.)
        self.code.append(Opcodes.EOC)
        return self.code


    def procedure(self, node, return_jump=True):
        address = self.address()
        [self.statement(child) for child in node.nodes]
        if return_jump:
            self.code.append(Opcodes.JMP)
        self.assert_node(node, Nodes.PROCEDURE)
        if node.lexeme.lower() in self.symtab:
            raise CodeError(
                f'Procedure {node.lexeme} defined more than once')
        else:
            self.symtab[node.lexeme.lower()] = address


    def statement(self, node):
        for node_type, handler in self.statement_handlers.items():
            res = (lambda x:x[1](node) if x[0] == node.node_type
                   else None)((node_type, handler))
            if res is not None:
                break


    def expression(self, node):
        if node.node_type == Nodes.CALL:
            self.handle_call(node)
        elif node.node_type == Nodes.INTEGER:
            self.code.append(int(node.lexeme))
        elif node.node_type == Nodes.OPERATOR:
            self.handle_operator(node)
        elif node.node_type == Nodes.VAR:
            self.code.append(self.var_opcode(node.lexeme))
 

    def handle_call(self, node):
        self.assert_node(node, Nodes.CALL)
        opcode = None
        expected_args = 0
        try:
            opcode = self.CALL_MAP[node.lexeme]
        except KeyError:
            pass
        finally:
            if opcode is not None:
                expected_args = Opcodes.nargs(opcode)

            actual_args = len(node.nodes)
            if expected_args != actual_args:
                if Opcodes.is_special(opcode) and actual_args == 0:
                    pass 
                else:
                    raise CodeError(
                            f'Expected {expected_args} ' +
                            f'parameters for {node.lexeme}. '+
                            f'Instead, got {actual_args} on ' +
                            f'{node.line},{node.column}')
            if opcode:
                if Opcodes.is_procedure(opcode): 
                    self.code.append(opcode)
                    if actual_args == 1:
                        self.expression(node.nodes[0])
                        self.code.append(Opcodes.ASS)
                else:
                    [self.expression(child) for child in node.nodes]
                    self.code.append(opcode)
            else:
                self.code.append(self.address() + 3) #Return address
                self.code.append(f'CALL_{node.lexeme.lower()}')
                self.code.append(Opcodes.JMP)


    def handle_if(self, root):
        def else_if(root):
            self.assert_node(root, Nodes.IF)
            cond = root.nodes[0]
            body = root.nodes[1]
            assert(len(root.nodes) < 3)
            self.expression(cond)
            end_address_pos = self.address()
            self.code.append(None)
            self.code.append(Opcodes.JIZ)
            [self.statement(node) for node in body.nodes]
            return end_address_pos


        self.assert_node(root, Nodes.IF)
        cond = root.nodes[0]
        body = root.nodes[1]
        elses = root.nodes[2:]
        self.expression(cond)
        else_address_pos = self.address()
        end_address_pos = set([else_address_pos])
        self.code.append(None)
        self.code.append(Opcodes.JIZ)
        [self.statement(node) for node in body.nodes]

        for node in elses:
            self.code[else_address_pos] = self.address() + 2
            end_address_pos.remove(else_address_pos)
            end_address_pos.add(self.address())
            self.code.append(None)
            self.code.append(Opcodes.JMP) 
            if node.node_type == Nodes.IF:
                else_address_pos = else_if(node)
                end_address_pos.add(else_address_pos)

            else:
                [self.statement(child) for child in node.nodes]
                break
        
        for pos in end_address_pos:
            self.code[pos] = self.address()


    def handle_operator(self, node):
        self.assert_node(node, Nodes.OPERATOR)
        operator = node.lexeme
        try:
            opcode = self.OPERATOR_MAP[operator]
        except KeyError:
            raise CodeError(
                    f'Unknown operator {operator} ' +
                    f'on {node.line},{node.column}')
        last_len = self.address()
        self.expression(node.nodes[0])
        
        if operator not in ('~', '!'):
            self.expression(node.nodes[1])
        elif (self.address() - last_len == 1 and
              node.nodes[0].node_type == Nodes.INTEGER):
            ## Unary operation optimization for integer operand
            self.code[-1] = (-self.code[-1] if operator == '~' else
                             int(not self.code[-1]))
            return
        self.code.append(opcode)
 

    def handle_return(self, node):
        self.assert_node(node, Nodes.RETURN)
        self.code.append(Opcodes.JMP)


    def handle_while(self, node):
        self.assert_node(node, Nodes.WHILE)
        self.code.append(self.address())
        self.expression(node.nodes[0])
        end_address_pos = self.address()
        self.code.append(None)
        self.code.append(Opcodes.JIZ)
        [self.statement(child) for child in node.nodes[1].nodes]
        self.code[end_address_pos] = self.address()


    def var_opcode(self, lexeme):
        return Opcodes.A + (ord(lexeme.lower()) - ord('a'))


    def assert_node(self, node, node_type):
        if node.node_type != node_type:
            raise CodeError(f'Unexpected node: {node_type}')


    def address(self):
        return len(self.code)

