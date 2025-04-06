from pathlib import Path

class VMWriter:

    operations = { 
        "+": "add", 
        "-": "sub", 
        "&": "and", 
        "|": "or", 
        "<": "lt", 
        ">": "gt", 
        "=": "eq",
        "neg": "neg"
    }
        # "not"

    def __init__(self, output_filename: str):
        file = Path(output_filename)
        if file.is_file():
            file.unlink()

        self.output_file = open(output_filename, "w")


    def write(self, code: str) -> None:
        self.output_file.write(code + "\n")
    

    def close(self) -> None:
        self.output_file.close()


    def push(self, tag: str, value: str) -> None:
        if tag == "integerConstant":
            self.write(f'push constant {value}')

    
    def push_variable(self, symbol_tuple) -> None:
        assert len(symbol_tuple) == 4
        
        VAR_NAME, _, var_kind, index = symbol_tuple
        if var_kind == "field":
            self.write(f'push this {index}')
        else:
            self.write(f'push {var_kind} {index}')


    def push_keyword_constant(self, keyword) -> None:
        if keyword == "this":
            self.write("push pointer 0")
            return
        
        self.write("push constant 0")
        if keyword == "true":
            self.write("not")


    def push_string(self, value) -> None:
        self.write(f'push constant {len(value)}')
        VMWriter.call("String.new", 1)

        for letter in value:
            self.write(f'push constant {ord(letter)}')
            VMWriter.call("String.appendChar", 2)


    def pop_to(self, symbol_tuple) -> None:
        assert len(symbol_tuple) == 4

        VAR_NAME, _, var_kind, index = symbol_tuple
        if var_kind == "field":
            self.write(f'pop this {index}')
        else:
            self.write(f'pop {var_kind} {index}')

    
    def perform_operation(self, symbol) -> None:
        if symbol not in VMWriter.operations:
            print(f'!!! Symbol {symbol} has no associated VM operation !!!')
        else:
            self.write(VMWriter.operations[symbol])

    
    def declare_func(self, func_name, n_params) -> None:
        self.write(f'function {func_name} {n_params}')
    
    
    def call(self, func_name, n_args) -> None:
        self.write(f'call {func_name} {n_args}')
    

    def return_func(self) -> None:
        self.write("return")
