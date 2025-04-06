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
        if keyword == "true":
            print("push constant 0")
            print("push constant 0")
            print("eq")
        elif keyword == "false":
            print("push constant 0")
            print("push constant 1")
            print("eq")
        else:
            print(f'!!! Need to implement VM command for keyword {keyword} !!!')


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
