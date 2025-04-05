class SymbolTable:

    class_var_kinds = ["field", "static"]
    subroutine_var_kinds = ["argument", "local"]

    def __init__(self):
        self.class_symbols = { kind: [] for kind in self.class_var_kinds }
        self.clear_subroutine_symbols()
        self.tables = [self.subroutine_symbols, self.class_symbols]

    
    def clear_subroutine_symbols(self) -> None:
        self.subroutine_symbols = { kind: [] for kind in self.subroutine_var_kinds }
    
    
    def add_symbol(self, symbol_details) -> None:
        var_name, var_type, var_kind = symbol_details
        if var_kind == "var":
            var_kind = "local"

        symbol_table = self.class_symbols if var_kind in self.class_var_kinds else self.subroutine_symbols
        kind_count = len(symbol_table[var_kind])

        symbol_table[var_kind].append((var_name, var_type, var_kind, kind_count))
