from typing import List, Union
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:

    token_idx = 0
    root = None
    node_stack = []

    op_symbols = { "+", "-", "*", "/", "&", "|", "<", ">", "=" }
    unary_op = { "-", "~" }
    keyword_constants = ["true", "false", "null", "this"]

    loop_counter = 0

    def  __init__(self, filename: str):
        tokens_tree = ET.parse(filename)
        self.output_filename = filename[:-5] + ".vm"
        self.tokens_root = tokens_tree.getroot()
        self.tokens_count = len(self.tokens_root)
        self.symbol_table = SymbolTable()


    def get_token(self, idx=None) -> (str, str):
        if not idx:
            idx = self.token_idx

        tag, value = self.tokens_root[idx].tag, self.tokens_root[idx].text
        if tag != "stringConstant":
            value = value.strip()
        
        return (tag, value)


    def next_token(self) -> None:
        self.token_idx += 1
    

    def get_parent_node(self) -> Union[ET.Element, None]:
        return self.node_stack[-1].tag if self.node_stack else None


    def add_parent_node(self, name: str) -> None:
        self.node_stack.append(ET.SubElement(self.node_stack[-1], name))


    def pop_parent_node(self) -> None:
        self.node_stack.pop()


    def compile_class(self, token: (str, str)) -> None:
        self.next_token()
        _, self.class_name = token = self.get_token()
        self.next_token()
        token = self.get_token()
        self.next_token()
        
        while self.get_parent_node() == "class":
            _, property_type = token = self.get_token()

            if token == ("symbol", "}"):
                self.next_token()
                self.pop_parent_node()

            if property_type in ["static", "field"]:
                self.compile_var(token)

            elif property_type in ["constructor", "function", "method"]:
                self.compile_subroutine(token, property_type)
            
            
    def compile_var(self, token: (str, str)) -> None:
        _, var_kind = token
        self.next_token()

        _, var_type = self.get_token()
        self.next_token()

        while token != ("symbol", ";"):
            _, var_name = token = self.get_token()
            if var_name not in [",", ";"]:
                self.symbol_table.add_symbol((var_name, var_type, var_kind))

            self.next_token()


    def compile_parameters(self, token: (str, str)) -> None:
        while token != ("symbol", ")"):
            _, var_type = token
            if var_type != ",":
                self.next_token()
                _, var_name = self.get_token()
                self.symbol_table.add_symbol((var_name, var_type, "argument"))

            self.next_token()
            token = self.get_token()


    def compile_subroutine(self, token: (str, str), subroutine_type: str) -> None:
        self.add_parent_node("subroutineDec")
        self.next_token()
        _, return_type = token = self.get_token()
        self.next_token()

        _, func_name = token = self.get_token()
        self.next_token()

        token = self.get_token()
        assert token == ("symbol", "(")
        self.next_token()
        
        self.add_parent_node("parameterList")
        token = self.get_token()

        if subroutine_type == "method":
            self.symbol_table.add_symbol(("this", self.class_name, "argument"))

        if token != ("symbol", ")"):
            self.compile_parameters(token)

        token = self.get_token()        
        self.pop_parent_node()
        self.next_token()

        func_declared = False

        self.add_parent_node("subroutineBody")
        assert self.get_token() == ("symbol", "{")
        self.next_token()

        while self.node_stack[-1].tag == "subroutineBody":
            _, property_type = token = self.get_token()

            if token == ("symbol", "}"):
                self.next_token()
                self.pop_parent_node()
                break

            # vars in subroutineBody will all be declared in the beginning
            while property_type == "var":
                self.compile_var(token)
                _, property_type = token = self.get_token()

            if not func_declared:
                if subroutine_type == "constructor":
                    fields_count = self.symbol_table.get_fields_count()
                    self.writer.declare_constructor(self.class_name, func_name, fields_count, self.symbol_table.get_local_vars_count())
                elif subroutine_type == "method":
                    self.writer.declare_method(self.class_name, func_name, self.symbol_table.get_local_vars_count())
                else:
                    self.writer.declare_func(self.class_name, func_name, self.symbol_table.get_local_vars_count())
                func_declared = True

            self.compile_statements()
        
        self.pop_parent_node()
        self.symbol_table.clear_subroutine_symbols()


    def compile_statements(self) -> None:
        self.add_parent_node("statements")

        while self.get_parent_node() == "statements":
            _, property_type = token = self.get_token()

            if token == ("symbol", "}"):
                self.pop_parent_node()

            if property_type == "let":
                self.compile_let(token)
            elif property_type == "do":
                self.compile_do(token)
            elif property_type == "return":
                self.compile_return(token)
            elif property_type == "if":
                self.compile_if(token)
            elif property_type == "while":
                self.compile_while(token)
            else:
                if property_type != "}":
                    print("Statement not implemented yet:", property_type)
                break

    
    def compile_while(self, token: (str, str)) -> None:
        self.add_parent_node("whileStatement")
        while token != ("symbol", "("):
            token = self.get_token()
            self.next_token()

        while_label, exit_label = self.loop_counter, self.loop_counter + 1
        self.loop_counter += 2

        self.writer.write(f'label L{while_label}')
        
        self.compile_expression(self.get_token())
        token = self.get_token()
        assert token[1] == ")"
        self.next_token()

        self.writer.write("not")
        self.writer.write(f'if-goto L{exit_label}')

        token = self.get_token()
        assert token[1] == "{"
        self.next_token()

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.next_token()

        self.writer.write(f'goto L{while_label}')
        self.writer.write(f'label L{exit_label}')

        self.pop_parent_node()


    def compile_if(self, token: (str, str)) -> None:
        self.add_parent_node("ifStatement")

        while token != ("symbol", "("):
            token = self.get_token()
            self.next_token()

        self.compile_expression(self.get_token())
        token = self.get_token()
        assert token[1] == ")"
        self.next_token()

        token = self.get_token()
        assert token[1] == "{"
        self.next_token()

        # TODO: move this code into VMWriter
        else_label, exit_label = self.loop_counter, self.loop_counter + 1
        self.loop_counter += 2

        self.writer.write("not")
        self.writer.write(f'if-goto L{else_label}')

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.next_token()

        self.writer.write(f'goto L{exit_label}')
        self.writer.write(f'label L{else_label}')

        token = self.get_token()
        if token == ("keyword", "else"):
            self.next_token()
            self.next_token()

            self.compile_statements()
            token = self.get_token()
            assert token[1] == "}"
            self.next_token()

        self.writer.write(f'label L{exit_label}')

        self.pop_parent_node()


    def compile_return(self, token: (str, str)) -> None:
        self.add_parent_node("returnStatement")

        assert token[1] == "return"
        self.next_token()
        
        token = self.get_token()
        if token != ("symbol", ";"):
            self.compile_expression(token)
        else:
            # push dummy value if not returning any actual value
            self.writer.push("integerConstant", 0)
        
        token = self.get_token()
        assert token[1] == ";"
        self.next_token()
        
        self.pop_parent_node()

        self.writer.return_func()


    def compile_do(self, token: (str, str)) -> None:
        self.add_parent_node("doStatement")
        self.next_token()
        _, func_name = token = self.get_token()
        self.compile_subroutine_call(token)

        self.next_token()
        token = self.get_token()
        assert token == ("symbol", ";")
        self.next_token()

        self.pop_parent_node()
        self.writer.pop_to(("", "", "temp", 0))


    def compile_let(self, token: (str, str)) -> None:
        self.add_parent_node("letStatement")
        self.next_token()

        kind, var_name = token = self.get_token()
        assert kind == "identifier"
        self.next_token()

        is_array = False

        token = self.get_token()
        if token == ("symbol", "["):
            is_array = True
            self.writer.push_variable(self.symbol_table.find_symbol(var_name))
            self.next_token()
            self.compile_expression(self.get_token())
            
            assert self.get_token() == ("symbol", "]")

            self.writer.perform_operation("+")

            self.next_token()
        
        assert self.get_token() == ("symbol", "=")

        while token != ("symbol", ";"):
            token = self.get_token()
            self.next_token()

            if token == ("symbol", "["):
                self.compile_expression(self.get_token())
                assert self.get_token() == ("symbol", "]")

                self.writer.perform_operation("+")
            elif token == ("symbol", "="):
                self.compile_expression(self.get_token())
                assert self.get_token() == ("symbol", ";")

        self.pop_parent_node()

        variable = self.symbol_table.find_symbol(var_name)
        if is_array:
            self.writer.pop_to(("", "", "temp", 0))
            self.writer.pop_to(("", "", "pointer", 1))
            self.writer.push_variable(("", "", "temp", 0))
            self.writer.pop_to(("", "", "that", 0))
        else:
            self.writer.pop_to(variable)


    def compile_expression_list(self, token: (str, str)) -> int:
        self.add_parent_node("expressionList")
        n_args = 0

        while token != ("symbol", ")"):
            if token == ("symbol", ","):
                self.next_token()
            else:
                self.compile_expression(token)
                n_args += 1

            token = self.get_token()

        self.pop_parent_node()
        return n_args


    def compile_expression(self, token: (str, str)) -> None:
        self.add_parent_node("expression")
        self.compile_term(token)
        self.next_token()

        tag, value = token = self.get_token()
        if tag == "symbol" and value in self.op_symbols:
            self.next_token()
            self.compile_term(self.get_token())
            self.next_token()
            if value == "*":
                self.writer.call("Math.multiply", 2)
            elif value == "/":
                self.writer.call("Math.divide", 2)
            else:
                self.writer.perform_operation(value)

        self.pop_parent_node()


    def compile_subroutine_call(self, token: (str, str)) -> None:
        tag, value = token

        subroutine_name, n_args = "", 0
        var = self.symbol_table.find_symbol(value)
        next_token = self.get_token(self.token_idx + 1)
        if next_token == ("symbol", ".") and var:
            self.writer.push_variable(var)
            subroutine_name = var[1]
            n_args += 1
        elif next_token != ("symbol", "."):
            self.writer.push("pointer", 0)
            subroutine_name = value
        else:
            subroutine_name = value

        self.next_token()
        _, val = token = self.get_token()

        while token != ("symbol", "("):
            subroutine_name += val
            self.next_token()
            _, val = token = self.get_token()

        self.next_token()
            
        n_args += self.compile_expression_list(self.get_token())
        token = self.get_token()
        assert token == ("symbol", ")")

        self.writer.call(subroutine_name, n_args, self.class_name)

    
    def compile_term(self, token: (str, str)) -> None:
        self.add_parent_node("term")
        tag, value = token
        next_tag, next_value = next_token = self.get_token(self.token_idx + 1)

        if tag == "integerConstant":
            self.writer.push(tag, value)
        elif tag == "stringConstant":
            self.writer.push_string(value[1:-1])
        elif tag == "keyword" and value in self.keyword_constants:
            self.writer.push_keyword_constant(value)
        elif tag == "identifier" and next_token == ("symbol", "."):
            self.compile_subroutine_call(token)
        elif tag == "identifier" and next_token == ("symbol", "("):
            self.next_token()
            self.compile_expression(self.get_token())
            token = self.get_token()
            assert token == ("symbol", ")")
        elif tag == "identifier" and next_token == ("symbol", "["):
            self.writer.push_variable(self.symbol_table.find_symbol(value))
            self.next_token()
            self.next_token()
            self.compile_expression(self.get_token())
            
            token = self.get_token()
            assert token == ("symbol", "]")

            self.writer.perform_operation("+")
            self.writer.pop_to(("", "", "pointer", 1))
            self.writer.push_variable(("", "", "that", 0))
        
        elif tag == "identifier":
            self.writer.push_variable(self.symbol_table.find_symbol(value))
        
        elif token == ("symbol", "("):
            self.next_token()
            self.compile_expression(self.get_token())

            token = self.get_token()
            assert token == ("symbol", ")")

        elif tag == "symbol" and value in self.unary_op:
            self.next_token()
            self.compile_term(self.get_token())

            if value == "-":
                self.writer.perform_operation("neg")
            else:
                self.writer.perform_operation(value)

        self.pop_parent_node()


    def compile(self) -> None:
        self.writer = VMWriter(self.output_filename)
        _, initial_value = self.get_token()
        assert initial_value == "class"

        root = ET.Element("class")
        self.node_stack.append(root)

        while self.token_idx < self.tokens_count:
            _, value = token = self.get_token()
            
            # class
            if value == "class":
                self.compile_class(token)
                continue

            self.next_token()
        
        self.writer.close()
