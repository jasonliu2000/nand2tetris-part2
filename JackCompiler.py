import sys
from pathlib import Path

from CompilationEngine import CompilationEngine
from JackTokenizer import tokenize

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py [filename|directory]")
        sys.exit(1)

    main_arg = sys.argv[1]

    if main_arg.endswith(".jack"):
        input_filename = main_arg
        if not Path(input_filename).is_file():
            print(f"Error: File '{input_filename}' not found.")
            sys.exit(1)

        tokenized_file = tokenize(input_filename)
        CompilationEngine(tokenized_file).compile()
            
    elif Path(main_arg).is_dir():
        directory = main_arg
        for file in Path(directory).iterdir():
            if file.name.endswith(".jack"):
                input_filename = f'{directory}/{file.name}'
                tokenized_file = tokenize(input_filename)
                CompilationEngine(tokenized_file).compile()
                
    else:
        print(f"Error: Input must either be a .jack file or a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()

    # SUGGESTION: test symbol table code first to ensure we're doing that correctly

    # input: .jack file or directory name
    # output: .vm file for every .jack file (stored within the directory if input was a directory name)

    # for every .jack file, the compiler creates a JackTokenizer and an output .vm file
    # compiler will then use SymbolTable, CompileEngine, and VMWriter to write the VM code into the output .vm file

    # compiler never needs > 2 symbol tables (just need 1 for class and 1 for subroutine)

    # tip: each symbol that's not in a symbol table can be safely assumed to be a subroutine or class name

    # VMWriter: 
    # - creates new output .vm file and prepares it for writing
    # - writes VM push/pop/label/... commands

    # CompilationEngine gets its input form JackTokenizer AND should use VMWriter's functions to write to the output file

    # vars:
        # - need context for each var to understand if it's a field, static, local, or arg variable
        # - also need to know if a var is the 1st, 2nd, 3rd, ... of its kind

        # class-level: field, static
        # subroutine-level: local, arg

        # see symbol table screenshot

        # if in subroutine and you encounter a var, first check in the subroutine symbol table for it, then the class symbol table for it
        # to handle this nested scoping, use a linkedlist of symbol tables and iterate from left to right when looking for te scope of var:
        #   scope 2 level ST --> scope 1 level ST --> method level ST --> class level ST
        # NOTE: in Jack, there will only be 2 levels: subroutine and class


    # expressions:
    # def code_write(exp):
    #     if exp.isdigit():
    #         return "push exp"
    #     if exp.is_VARIABLE():
    #         return "push exp"
    #     if exp like "exp1 op exp2":
    #         code_write("exp1")
    #         code_write("exp2")
    #         return "op"
    #     if exp like "op exp": # like unary operator
    #         code_write(exp)
    #         return "op" # unary operator
    #     if exp like "f(exp1, exp2, ...)":
    #         code_write(exp1)
    #         code_write(exp2)
    #         # ...
    #         return "call f"
            
            # jack language has no specification for mathematical order of operations, except for priority towards expressions in parentheses


    # statements (flow of control):
        # see if-statement screenshot
        # while-statement would be similar to how if-statement would be implemented
        # ensure generated labels are unique (don't want one if-statement to actually end up going into some other while-statement)
        # if and while statements are often nested (make recursive)


    # object/array data:
        # to add some value to an object...
        # push some value from the heap (where object data and arrays will be stored in the RAM, e.g. 8000) to the stack
        # and then pop it to pointer 0. (RAM[THIS] = 8000)
        # now if you want to add some value to the object, just do:
        # push 17
        # pop this 0 (THIS is pointed to 8000, so 17 is popped to 8000 + 0 = 8000 in RAM)
        # (this sets RAM[8000] = 17)

        # to add some value to an array, just do the same as above but replace this/THIS with that/THAT

    
    # object construction:
        # 2 steps: 
            # 1) declare variable of type object: var Point p1;
            # 2) initialize variable to the object: let p1 = Point.new();

    # object methods: (NOT THE CASE FOR OBJECT FUNCTIONS)
        # to compile a call to an object method...
        # first push the object to the stack, then its arguments, then call the function itself
        # e.g. obj.foo(x1, x2, ...) -> push obj ; push x1 ; push x2 ; push ... ; call foo

        # to compile an object method declaration...
        # first add the class to the method-level symbol table with name "this", type "[class name]" and kind "argument"!!!
        # then add the method arguments and local vars to the symbol table
        # (see screenshot)

        # !!!! WHEN COMPILING VOID METHODS/FUNCTIONS, "push constant 0" before returning. Then, after we called the void method, we want to immediately pop this constant 0 form the stack into some random place (e.g. pop temp 0)
        # !!!! and remember to consider this when you call a void function (pop dummy value that the void function you called appended to the stack to temp 0)


    # array:
        # when we declare an array, add it to symbol table with type Array
        # suggestion: use this to represent values of the current OBJECT, use that to represent values of the current ARRAY
        # recall: "pop pointer 0" i used to set THIS (which is the pointer holding the base address of this). Similarly, use 1 instead of 0 for that/THAT


    # misc:
        # use Math.multiply() for multiplication, Math.divide(), String.new() for new strings, String.appendChar(c) for x = "c"
        # use Memory.alloc(size) to allocate space for a new object
        # use Memory.dealloc(object) to handle object recycling
        # null and false are mapped to constant 0; true is mapped to constant -1 (push 1; neg)
