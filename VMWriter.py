class VMWriter:

    operations = { 
        "+": "add", 
        "-": "sub", 
        "&": "and", 
        "|": "or", 
        "<": "lt", 
        ">": "gt", 
        "=": "eq"
    }
        # "not"

    def push(tag: str, value: str) -> None:
        if tag == "integerConstant":
            print(f'push constant {value}')

    
    def push_variable(symbol_tuple) -> None:
        assert len(symbol_tuple) == 4
        
        VAR_NAME, _, var_kind, index = symbol_tuple
        if var_kind == "field":
            print(f'push this {index}', f'| {var_kind} {VAR_NAME}')
        else:
            print(f'push {var_kind} {index}', f'| {var_kind} {VAR_NAME}')


    def push_keyword_constant(keyword) -> None:
        if keyword == "this":
            print("push pointer 0")
            return
        
        print("push constant 0")
        
        if keyword == "true":
            print("not")


    def push_string(value) -> None:
        print(f'push constant {len(value)}')
        VMWriter.call("String.new", 1)

        for letter in value:
            print(f'push constant {ord(letter)}')
            VMWriter.call("String.appendChar", 2)


    def pop_to(symbol_tuple) -> None:
        assert len(symbol_tuple) == 4

        VAR_NAME, _, var_kind, index = symbol_tuple
        if var_kind == "field":
            print(f'pop this {index}', f'| {var_kind} {VAR_NAME}')
        else:
            print(f'pop {var_kind} {index}', f'| {var_kind} {VAR_NAME}')

    
    def perform_operation(symbol) -> None:
        if symbol not in VMWriter.operations:
            print(f'!!! Symbol {symbol} has no mapping VM operation !!!')
        else:
            print(VMWriter.operations[symbol])

    
    def declare_func(func_name, n_params) -> None:
        print(f'function {func_name} {n_params}')
    
    
    def call(func_name, n_args) -> None:
        print(f'call {func_name} {n_args}')
    

    def return_func() -> None:
        print("return")
