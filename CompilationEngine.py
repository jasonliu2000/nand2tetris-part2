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


    def write_to_xml(self, token: (str, str)) -> None:
        tag, value = token
        ET.SubElement(self.node_stack[-1], tag).text = f' {value} ' if tag != "stringConstant" else value
    

    def get_parent_node(self) -> Union[ET.Element, None]:
        return self.node_stack[-1].tag if self.node_stack else None


    def add_parent_node(self, name: str) -> None:
        self.node_stack.append(ET.SubElement(self.node_stack[-1], name))


    def pop_parent_node(self) -> None:
        self.node_stack.pop()


    def compile_class(self, token: (str, str)) -> None:
        self.write_to_xml(token)
        self.token_idx += 1

        _, self.class_name = token = self.get_token()
        self.write_to_xml(token)
        self.token_idx += 1

        token = self.get_token()
        self.write_to_xml(token)
        self.token_idx += 1
        
        while self.get_parent_node() == "class":
            _, property_type = token = self.get_token()

            if token == ("symbol", "}"):
                self.write_to_xml(token)
                self.token_idx += 1
                self.pop_parent_node()

            if property_type in ["static", "field"]:
                self.compile_var(token)

            elif property_type in ["constructor", "function", "method"]:
                self.compile_subroutine(token, property_type)
            
            
    def compile_var(self, token: (str, str)) -> None:
        _, var_kind = token
        self.token_idx += 1

        _, var_type = self.get_token()
        self.token_idx += 1

        while token != ("symbol", ";"):
            _, var_name = token = self.get_token()
            if var_name not in [",", ";"]:
                print((var_name, var_type, var_kind))
                self.symbol_table.add_symbol((var_name, var_type, var_kind))

            self.token_idx += 1


    def compile_parameters(self, token: (str, str)) -> None:
        while token != ("symbol", ")"):
            _, var_type = token
            if var_type != ",":
                self.token_idx += 1
                _, var_name = self.get_token()
                self.symbol_table.add_symbol((var_name, var_type, "argument"))

            self.token_idx += 1
            token = self.get_token()


    def compile_subroutine(self, token: (str, str), subroutine_type: str) -> None:
        self.add_parent_node("subroutineDec")

        self.write_to_xml(token)
        self.token_idx += 1

        _, return_type = token = self.get_token()
        self.write_to_xml(token)
        self.token_idx += 1

        _, func_name = token = self.get_token()
        self.write_to_xml(token)
        self.token_idx += 1

        token = self.get_token()
        assert token == ("symbol", "(")
        self.write_to_xml(token)
        self.token_idx += 1
        
        self.add_parent_node("parameterList")
        token = self.get_token()

        if subroutine_type == "method":
            self.symbol_table.add_symbol(("this", self.class_name, "argument"))

        if token != ("symbol", ")"):
            self.compile_parameters(token)

        token = self.get_token()        
        self.pop_parent_node()
        self.write_to_xml(token)
        self.token_idx += 1

        func_declared = False

        self.add_parent_node("subroutineBody")
        assert self.get_token() == ("symbol", "{")
        self.write_to_xml(self.get_token())
        self.token_idx += 1

        while self.node_stack[-1].tag == "subroutineBody":
            _, property_type = token = self.get_token()

            if token == ("symbol", "}"):
                self.write_to_xml(token)
                self.token_idx += 1
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
        
        # print(self.symbol_table.subroutine_symbols)
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
            self.write_to_xml(token)
            self.token_idx += 1

        while_label, exit_label = self.loop_counter, self.loop_counter + 1
        self.loop_counter += 2

        self.writer.write(f'label L{while_label}')
        
        self.compile_expression(self.get_token(), [("symbol", ")")])
        token = self.get_token()
        assert token[1] == ")"
        self.write_to_xml(token)
        self.token_idx += 1

        self.writer.write("not")
        self.writer.write(f'if-goto L{exit_label}')

        token = self.get_token()
        assert token[1] == "{"
        self.write_to_xml(token)
        self.token_idx += 1

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.write_to_xml(token)
        self.token_idx += 1

        self.writer.write(f'goto L{while_label}')
        self.writer.write(f'label L{exit_label}')

        self.pop_parent_node()


    def compile_if(self, token: (str, str)) -> None:
        self.add_parent_node("ifStatement")

        while token != ("symbol", "("):
            token = self.get_token()
            self.write_to_xml(token)
            self.token_idx += 1

        self.compile_expression(self.get_token(), [("symbol", ")")])
        token = self.get_token()
        assert token[1] == ")"
        self.write_to_xml(token)
        self.token_idx += 1

        token = self.get_token()
        assert token[1] == "{"
        self.write_to_xml(token)
        self.token_idx += 1

        # TODO: move this code into VMWriter
        else_label, exit_label = self.loop_counter, self.loop_counter + 1
        self.loop_counter += 2

        self.writer.write("not")
        self.writer.write(f'if-goto L{else_label}')

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.write_to_xml(token)
        self.token_idx += 1

        self.writer.write(f'goto L{exit_label}')
        self.writer.write(f'label L{else_label}')

        token = self.get_token()
        if token == ("keyword", "else"):
            self.write_to_xml(token)
            self.token_idx += 1
            self.write_to_xml(self.get_token())
            self.token_idx += 1

            self.compile_statements()
            token = self.get_token()
            assert token[1] == "}"
            self.write_to_xml(token)
            self.token_idx += 1

        self.writer.write(f'label L{exit_label}')

        self.pop_parent_node()


    def compile_return(self, token: (str, str)) -> None:
        self.add_parent_node("returnStatement")

        assert token[1] == "return"
        self.write_to_xml(token)
        self.token_idx += 1
        
        token = self.get_token()
        if token != ("symbol", ";"):
            self.compile_expression(token, [("symbol", ";")])
        else:
            # push dummy value if not returning any actual value
            self.writer.push("integerConstant", 0)
        
        token = self.get_token()
        assert token[1] == ";"
        self.write_to_xml(token)
        self.token_idx += 1
        
        self.pop_parent_node()

        self.writer.return_func()


    def compile_do(self, token: (str, str)) -> None:
        self.add_parent_node("doStatement")

        self.write_to_xml(token)
        self.token_idx += 1

        _, func_name = token = self.get_token()

        self.compile_subroutine_call(token)

        self.token_idx += 1
        token = self.get_token()
        assert token == ("symbol", ";")
        self.write_to_xml(token)
        self.token_idx += 1

        self.pop_parent_node()
        self.writer.pop_to(("", "", "temp", 0))


    def compile_let(self, token: (str, str)) -> None:
        self.add_parent_node("letStatement")
        
        self.write_to_xml(token)
        self.token_idx += 1

        kind, var_name = token = self.get_token()
        assert kind == "identifier"
        self.write_to_xml(token)
        self.token_idx += 1

        is_array = False

        token = self.get_token()
        if token == ("symbol", "["):
            is_array = True
            self.writer.push_variable(self.symbol_table.find_symbol(var_name))
            self.token_idx += 1
            self.compile_expression(self.get_token(), [("symbol", "]")])
            
            assert self.get_token() == ("symbol", "]")

            self.writer.perform_operation("+")

            self.token_idx += 1
        
        assert self.get_token() == ("symbol", "=")

        while token != ("symbol", ";"):
            token = self.get_token()
            self.write_to_xml(token)
            self.token_idx += 1

            if token == ("symbol", "["):
                self.compile_expression(self.get_token(), [("symbol", "]")])
                assert self.get_token() == ("symbol", "]")

                self.writer.perform_operation("+")
            elif token == ("symbol", "="):
                self.compile_expression(self.get_token(), [("symbol", ";")])
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
        end_tokens = [("symbol", ","), ("symbol", ")")]
        n_args = 0

        while token != ("symbol", ")"):
            if token == ("symbol", ","):
                self.write_to_xml(token)
                self.token_idx += 1
            else:
                self.compile_expression(token, end_tokens)
                n_args += 1

            token = self.get_token()

        self.pop_parent_node()
        return n_args


    def compile_expression(self, token: (str, str), end_on: [(str, str)]) -> None: # TODO: remove end_on
        self.add_parent_node("expression")
        self.compile_term(token)
        self.token_idx += 1

        tag, value = token = self.get_token()
        if tag == "symbol" and value in self.op_symbols:
            self.write_to_xml(token)
            self.token_idx += 1
            self.compile_term(self.get_token())
            self.token_idx += 1
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
        else:
            subroutine_name = value

        self.token_idx += 1
        _, val = token = self.get_token()

        while token != ("symbol", "("):
            subroutine_name += val

            self.write_to_xml(token)
            self.token_idx += 1
            _, val = token = self.get_token()

        self.write_to_xml(token)
        self.token_idx += 1
            
        n_args += self.compile_expression_list(self.get_token())
        token = self.get_token()
        assert token == ("symbol", ")")
        self.write_to_xml(token)

        self.writer.call(subroutine_name, n_args, self.class_name)

    
    def compile_term(self, token: (str, str)) -> None:
        self.add_parent_node("term")
        tag, value = token
        self.write_to_xml(token)

        next_tag, next_value = next_token = self.get_token(self.token_idx + 1)

        if tag == "integerConstant":
            self.writer.push(tag, value)
            # self.token_idx += 1
        elif tag == "stringConstant":
            self.writer.push_string(value)
        elif tag == "keyword" and value in self.keyword_constants:
            self.writer.push_keyword_constant(value)
            # self.token_idx += 1
        # elif tag == "identifier" and next_tag == "symbol" and next_value in self.op_symbols:

        elif tag == "identifier" and next_token == ("symbol", "."):
            self.compile_subroutine_call(token)
        elif tag == "identifier" and next_token == ("symbol", "("):
            self.token_idx += 1
            self.write_to_xml(self.get_token())
            self.compile_expression(self.get_token(), [("symbol", ")")])
            token = self.get_token()
            assert token == ("symbol", ")")
        elif tag == "identifier" and next_token == ("symbol", "["):
            self.writer.push_variable(self.symbol_table.find_symbol(value))
            self.write_to_xml(next_token)
            self.token_idx += 2
            self.compile_expression(self.get_token(), [("symbol", "]")])
            
            token = self.get_token()
            assert token == ("symbol", "]")
            self.write_to_xml(token)
            # self.token_idx += 1

            self.writer.perform_operation("+")
            self.writer.pop_to(("", "", "pointer", 1))
            self.writer.push_variable(("", "", "that", 0))
        
        elif tag == "identifier":
            self.writer.push_variable(self.symbol_table.find_symbol(value))
        
        elif token == ("symbol", "("):
            self.token_idx += 1
            self.compile_expression(self.get_token(), [("symbol", ")")])

            token = self.get_token()
            assert token == ("symbol", ")")
            self.write_to_xml(token)
            # self.token_idx += 1

        elif tag == "symbol" and value in self.unary_op:
            self.token_idx += 1
            self.compile_term(self.get_token())
            # self.token_idx += 1

            if value == "-":
                self.writer.perform_operation("neg")
            else:
                self.writer.perform_operation(value)

        elif tag == "keyword":
            self.write_to_xml(token)
            # self.token_idx += 1
        
        # self.token_idx += 1

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

            self.token_idx += 1

        # tree = ET.ElementTree(root)
        # tree.write(self.output_filename)
        # self.prettify_xml(self.output_filename)

        # TODO: remove
        for table in self.symbol_table.tables:
            print(table)
        
        self.writer.close()


    def prettify_xml(self, file_path):
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Expand empty tags
        self.expand_empty_tags(root)

        # Convert to string
        rough_string = ET.tostring(root, 'utf-8')

        # Pretty print with minidom
        parsed = parseString(rough_string)
        pretty_xml = parsed.toprettyxml(indent="  ")  # Two spaces for indentation
        
        # Write to output file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(pretty_xml.split("\n")[1:]))

    def expand_empty_tags(self, element):
        for child in element:
            self.expand_empty_tags(child)  # Process children recursively
        
        if not element.text and not list(element):  # If the tag is empty
            element.text = "\n"  # Add a newline to force expansion