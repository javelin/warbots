# -*- coding: utf-8 -*-

import re

from code import CodeGenerator
from opcodes import Opcodes
from version import Versions
try:
    from parser import Parser
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(os.getcwd()))
    from wb.parser import Parser


class CompileError(Exception): pass


class Compiler(object):
    def __init__(self, source):
        self.parser = Parser(source)
        self.code = []
 

    def reset(self):
        self.parser.reset()
        self.code = []


    def compile(self, version=Versions.V2_0_0):
        self.reset()
        codegen = CodeGenerator(self.parser.parse(), version=version)
        try:
            self.code = codegen.generate()
        except:
            self.code = codegen.code
            raise
        else:
            return self.code


if __name__ == '__main__':
    import sys
    from traceback import print_exc
    from utils import prettify_code
    
    try:
        with open(sys.argv[1], 'rt') as f:
            scode = f.read()
            c = Compiler(scode)
            try:
                c.compile()
            except:
                print_exc()
                print('Incomplete code output:')
            finally:
                print(prettify_code(c.code))
    except:
        print_exc()

