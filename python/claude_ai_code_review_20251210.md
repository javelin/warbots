# Warbots Compiler Code Analysis

## Overview

This is a complete compiler implementation for **Warbots**, a programming game where players write AI scripts to control combat robots. The compiler translates a C-like language into bytecode that runs on a virtual machine.

## Architecture

### Core Components

```
Source Code → Tokenizer → Parser → Code Generator → Bytecode
```

1. **Tokenizer** (`tokenizer.py`) - Lexical analysis
2. **Parser** (`parser.py`) - Syntax analysis & AST generation
3. **Code Generator** (`code.py`) - Bytecode emission
4. **Compiler** (`compiler.py`) - Orchestration layer
5. **Opcodes** (`opcodes.py`) - VM instruction set
6. **File I/O** (`wb.py`, `read.py`) - Binary format handling

---

## Component Analysis

### 1. Tokenizer (`tokenizer.py`)

**Purpose**: Converts source text into tokens

**Features**:
- State machine implementation with 10 states
- Handles comments (line `//` and block `/* */`)
- Tracks line/column positions for error reporting
- Reserved keyword recognition
- Single-letter variable detection (a-z)

**Token Types** (31 total):
- Keywords: `if`, `else`, `while`, `return`
- Operators: `+`, `-`, `*`, `/`, `%`, `!`, `&`, `|`, `^`
- Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Delimiters: `{`, `}`, `(`, `)`, `;`, `,`
- Literals: integers, identifiers, variables

**Notable Design Decisions**:
- Variables are limited to single letters (a-z)
- No string literals or floating-point support
- Line tracking for error messages

**Issues**:
- `unget()` method has complex logic for column recalculation that could be fragile
- No error recovery mechanism for invalid characters
- The `IN_BANG` state returns wrong token when `!=` is parsed (missing lexeme concatenation)

---

### 2. Parser (`parser.py`)

**Purpose**: Builds an Abstract Syntax Tree (AST) from tokens

**Grammar** (simplified):
```
program    → procedure*
procedure  → IDENTIFIER '{' statement* '}'
statement  → block | assignment | call | if | while | return
expression → logical_expr → comparative_expr → arithmetic_expr → term → factor
```

**AST Node Types**:
- `PROGRAM` - Root node
- `PROCEDURE` - Function definitions
- `BLOCK` - Statement grouping
- `CALL` - Function calls
- `IF` - Conditional with optional else/else-if chains
- `WHILE` - Loop construct
- `RETURN` - Early exit
- `OPERATOR` - Binary/unary operations
- `VAR` - Variable reference
- `INTEGER` - Literal values

**Operator Precedence** (low to high):
1. Logical: `&`, `|`, `^`
2. Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
3. Arithmetic: `+`, `-`
4. Multiplicative: `*`, `/`, `%`
5. Unary: `-` (negation), `!` (not)

**Strengths**:
- Clean recursive descent implementation
- Proper precedence handling
- Good error messages with line/column info

**Issues**:
- **Critical Bug** in `logical_expr()` line ~325: Missing comma in tuple causes syntax error:
  ```python
  Node(Nodes.OPERATOR, self.last_line, self.last_column, '&'
       (node.nodes[-1], self.comparative_expr()))  # Missing comma after '&'!
  ```
- Special case for `&` operator associativity seems incomplete/buggy
- No semantic analysis (type checking, variable declaration checking)
- Allows undefined function calls without validation

---

### 3. Code Generator (`code.py`)

**Purpose**: Converts AST to bytecode

**Key Features**:
- Symbol table for procedure addresses
- Forward reference resolution (for procedure calls)
- Optimization: unary operations on constants folded at compile time
- Special handling for "overloaded" functions (can be called with 0 or 1 arguments)

**Instruction Categories**:

1. **Special Variables** (can be read or written):
   - Position: `xpos`, `ypos`
   - Status: `collision`, `damage`, `energy`, `radar`, `range`
   - Controls: `aim`, `channel`, `speedx`, `speedy`, `shield`, `signal`

2. **Functions**:
   - `arctan(x, y)` - 2 arguments
   - `sqrt(x)` - 1 argument
   - `random()` - 0 arguments

3. **Procedures** (return void):
   - Weapons: `fire(e)`, `missile(e)`, `nuke(e)`
   - Movement: `movex(d)`, `movey(d)`
   - Configuration: `aim(a)`, `speedx(s)`, `speedy(s)`, `shield(s)`, `channel(c)`, `signal(s)`

4. **Operators**:
   - Arithmetic: `+`, `-`, `*`, `/`, `%`
   - Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
   - Logical: `&`, `|`, `^`, `!`
   - Unary: `-` (negate), `!` (not)

**Code Generation Strategy**:
- Stack-based evaluation
- Always generates `main` and optionally `init` first
- `init` doesn't generate a return jump (optimization)
- Call addresses filled in second pass

**Issues**:
- Import error handling uses broad `except ImportError` which might mask other issues
- `handle_while()` has a bug: pushes loop start address to code instead of generating proper jump-back
- Missing loop start label for while loop back-edge
- Assignment operator handling could be clearer
- No dead code elimination

---

### 4. Opcodes (`opcodes.py`)

**Purpose**: Defines the VM instruction set

**Instruction Ranges**:
- `0x7f5a-0x7f71`: Control flow & operators (25 opcodes)
- `0x7f77-0x7f8b`: Game functions (21 opcodes)
- `0x7f95-0x7fae`: Variables A-Z (26 opcodes)

**Notable Instructions**:
- `JMP (0x7f5a)` - Unconditional jump
- `JIZ (0x7f5e)` - Jump if zero
- `EOC (0x7f5b)` - End of code marker
- `ASS (0x7f5f)` - Assignment
- Planned but unused: `INC`, `DEC`, `SLEEP`, `SKIP`

**Helper Functions**:
- `is_special()` - Checks if opcode is read/writable
- `is_procedure()` - Checks if opcode returns void
- `is_function()` - Checks if opcode returns value
- `nargs()` - Returns expected argument count

**Design Notes**:
- Uses Python's `IntEnum` for type safety
- Opcodes deliberately placed in high memory range (0x7f00+) to avoid collision with integer literals
- Clear separation between procedures (side effects) and functions (return values)

---

### 5. Binary Format (`wb.py`, `read.py`)

**File Format**: `.bot` files

**Structure** (offsets in bytes):
```
0x0000: Header (8 bytes)      - "WBMD2.0\0"
0x0008: Name (20 bytes)        - Bot name (null-terminated)
0x001C: Unknown (8 bytes)      - Reserved/unused
0x0024: Energy (2 bytes)       - 0=High, 1=Normal, 2=Low, 3=None
0x0026: Shield (2 bytes)       - Same scale
0x0028: Armor (2 bytes)        - 0=Strong, 1=Normal, 2=Weak, 3=Very Weak
0x002A: CPU Speed (2 bytes)    - 0=25cpc, 1=20cpc, 2=15cpc, 3=10cpc
0x002C: Bullet Type (2 bytes)  - 0=Explosive, 1=Normal, 2=Rubber
0x002E: Has Missiles (1 byte)  - Boolean
0x002F: Has Nukes (1 byte)     - Boolean
0x0030: Icon 1 (1024 bytes)    - 32x32 bitmap?
0x0430: Icon 2 (1024 bytes)    - Second icon
0x0830: Is Compiled (1 byte)   - Boolean flag
0x0834: Bytecode Size (2 bytes)- Number of 2-byte words
0x0836: Bytecode (variable)    - Compiled code
       Source Code (remaining) - Null-terminated source
```

**Key Insights**:
- Stores both compiled bytecode AND source code
- Allows runtime toggle between interpreted/compiled modes
- Bot attributes affect gameplay (energy, speed, weapons)
- Icons stored as raw bitmaps

---

## Language Features

### Example Program Analysis

```javascript
// From baal_source.txt
main {
  aim(53);           // Set turret angle
  seek;              // Call procedure
  if (collision) suicide;
  if (xpos > 260) speedx(-3);
  else if (xpos < 40) speedx(3);
}

init {
  if (xpos > 150) speedx(3);
  else speedx(-3);
}

seek {
  if (range & energy > 50) {
    shield(5);
    while(range & energy > 10) fire(energy/2);
  }
}

suicide {
  while (!range) {
    aim(aim + 15);
    if (!collision) return;
  }
  shield(5);
  while (range) fire(energy/2);
}
```

**Language Characteristics**:
- C-like syntax with braces and semicolons
- No function parameters (uses global state)
- No return values (procedures only)
- Implicit state sharing between procedures
- Mix of imperative commands and sensor queries

**Built-in State Variables**:
- **Sensors**: `collision`, `damage`, `energy`, `radar`, `range`, `xpos`, `ypos`
- **Actuators**: `aim`, `speedx`, `speedy`, `shield`, `channel`, `signal`
- **User Variables**: `a-z` (26 single-letter variables)

---

## Compilation Process

### Phases

1. **Tokenization**
   ```
   "if (xpos > 100)" → [IF, LPAREN, IDENTIFIER, GT, INTEGER, RPAREN]
   ```

2. **Parsing**
   ```
   IF
   ├── OPERATOR (>)
   │   ├── CALL (xpos)
   │   └── INTEGER (100)
   └── BLOCK
       └── [statements...]
   ```

3. **Code Generation**
   ```
   XPOS      // Push xpos value
   100       // Push constant
   GT        // Compare
   addr      // Jump target if false
   JIZ       // Jump if zero
   [body]    // Statement body
   ```

### Optimization Techniques

1. **Constant Folding**: Unary operations on constants evaluated at compile time
   ```python
   -5  → generates: 32763  (not: 5, NEG)
   !0  → generates: 1      (not: 0, NOT)
   ```

2. **Init Optimization**: No jump instruction from `init` to `main` (falls through)

3. **Forward References**: Procedure calls use placeholder addresses filled in second pass

---

## Bugs and Issues

### Critical Bugs

1. **Parser Bug** (`parser.py:325`):
   ```python
   # Missing comma causes syntax error
   Node(Nodes.OPERATOR, self.last_line, self.last_column, '&'
        (node.nodes[-1], self.comparative_expr()))
   # Should be: '&',
   ```

2. **While Loop Bug** (`code.py`):
   ```python
   def handle_while(self, node):
       self.code.append(self.address())  # Pushes address as data!
       # Should generate: loop_start = self.address()
       # And later: JMP to loop_start
   ```

3. **Tokenizer NOT_EQUAL Bug**:
   ```python
   elif state == States.IN_BANG:
       if c == '=':
           return Tokens.NOT_EQUAL  # Missing lexeme + c
   ```

### Design Issues

1. **No Type System**: Variables can hold any integer value; no compile-time checks
2. **No Scoping**: All variables are global
3. **No Error Recovery**: First error terminates compilation
4. **Limited Error Messages**: Some errors don't specify what was expected
5. **Implicit Procedure Declaration**: Can call undefined procedures (will fail at runtime)
6. **Magic Numbers**: Opcode values should be more clearly documented

### Code Quality Issues

1. **Inconsistent Error Handling**: Mix of exceptions and None returns
2. **Duplicate Code**: `wb.py` and `read.py` are nearly identical
3. **Hardcoded Paths**: Import fallback logic assumes specific directory structure
4. **No Documentation**: Missing docstrings for most functions
5. **Testing**: No unit tests visible in codebase

---

## Strengths

1. **Clean Architecture**: Well-separated concerns (lexer, parser, codegen)
2. **Simple Language**: Easy to learn and debug
3. **Complete Pipeline**: Handles entire compilation process
4. **Error Reporting**: Line/column tracking for debugging
5. **Extensible**: Easy to add new opcodes or language features
6. **Practical**: Solves real problem (game AI scripting)

---

## Recommendations

### Immediate Fixes

1. Fix the critical parser bug in `logical_expr()`
2. Fix the while loop code generation
3. Add proper import statements (remove try/except fallbacks)
4. Fix tokenizer's `NOT_EQUAL` token generation

### Short-term Improvements

1. Add comprehensive unit tests
2. Implement proper error recovery in parser
3. Add semantic analysis phase (variable declaration checking)
4. Document the binary file format specification
5. Add command-line interface for standalone compilation

### Long-term Enhancements

1. Add local variables and procedure parameters
2. Implement optimization passes (dead code elimination, constant propagation)
3. Add debugger support (breakpoints, step execution)
4. Create standard library of common bot behaviors
5. Add type system for better compile-time error detection
6. Generate better VM instructions (reduce code size)

---

## Performance Considerations

**Compilation Speed**: Fast for typical bot programs (< 100 lines)
- Tokenizer: O(n) single pass
- Parser: O(n) recursive descent
- Code Generation: O(n) with O(n) symbol resolution

**Output Size**: Compact bytecode
- Average bot: 50-200 instructions
- Each instruction: 2 bytes
- Total: 100-400 bytes typical

**Memory Usage**: Minimal
- No heap allocation during compilation
- Linear memory growth with input size
- Symbol table size = number of procedures

---

## Conclusion

This is a **well-structured educational compiler** that demonstrates core compilation concepts. The language is simple but sufficient for its domain (robot AI). The codebase has some bugs but shows good architectural decisions.

**Best Use Case**: Teaching compiler construction or rapid prototyping of game AI

**Maturity Level**: Late alpha / early beta - functional but needs bug fixes and testing

**Code Quality**: 6/10 - Good structure, needs polish and documentation
