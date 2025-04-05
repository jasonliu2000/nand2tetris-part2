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

    def __init__(self, filename: str):
        tokens_tree = ET.parse(filename)
        self.output_filename = filename[:-5] + ".xml"
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
        _, var_kind = self.get_token()
        self.token_idx += 1

        _, var_type = self.get_token()
        self.token_idx += 1

        while token != ("symbol", ";"):
            _, var_name = token = self.get_token()
            if var_name not in [",", ";"]:
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
        while token != ("symbol", "("):
            token = self.get_token()
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
        
        self.compile_expression(self.get_token(), [("symbol", ")")])
        token = self.get_token()
        assert token[1] == ")"
        self.write_to_xml(token)
        self.token_idx += 1

        token = self.get_token()
        assert token[1] == "{"
        self.write_to_xml(token)
        self.token_idx += 1

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.write_to_xml(token)
        self.token_idx += 1

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

        self.compile_statements()
        token = self.get_token()
        assert token[1] == "}"
        self.write_to_xml(token)
        self.token_idx += 1

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

        self.pop_parent_node()


    def compile_return(self, token: (str, str)) -> None:
        self.add_parent_node("returnStatement")

        assert token[1] == "return"
        self.write_to_xml(token)
        self.token_idx += 1
        
        token = self.get_token()
        if token != ("symbol", ";"):
            self.compile_expression(token, [("symbol", ";")])
        
        token = self.get_token()
        assert token[1] == ";"
        self.write_to_xml(token)
        self.token_idx += 1
        
        self.pop_parent_node()


    def compile_do(self, token: (str, str)) -> None:
        self.add_parent_node("doStatement")
        while token != ("symbol", ";"):
            token = self.get_token()
            self.write_to_xml(token)
            self.token_idx += 1

            if token == ("symbol", "("):
                self.compile_expression_list(self.get_token())
                token = self.get_token()
                assert token == ("symbol", ")")
                self.write_to_xml(token)
                self.token_idx += 1

        self.pop_parent_node()
    

    def compile_let(self, token: (str, str)) -> None:
        self.add_parent_node("letStatement")
        
        self.write_to_xml(token)
        self.token_idx += 1

        kind, var_name = token = self.get_token()
        assert kind == "identifier"
        self.write_to_xml(token)
        self.token_idx += 1

        token = self.get_token()

        while token != ("symbol", ";"):
            token = self.get_token()
            self.write_to_xml(token)
            self.token_idx += 1

            if token == ("symbol", "["):
                self.compile_expression(self.get_token(), [("symbol", "]")])
            elif token == ("symbol", "="):
                self.compile_expression(self.get_token(), [("symbol", ";")])

        self.pop_parent_node()

        variable = self.symbol_table.find_symbol(var_name)
        VMWriter.pop_to(variable)
    

    def compile_expression_list(self, token: (str, str)) -> None:
        self.add_parent_node("expressionList")
        end_tokens = [("symbol", ","), ("symbol", ")")]

        while token != ("symbol", ")"):
            if token == ("symbol", ","):
                self.write_to_xml(token)
                self.token_idx += 1
            else:
                self.compile_expression(token, end_tokens)

            token = self.get_token()

        self.pop_parent_node()


    def compile_expression(self, token: (str, str), end_on: [(str, str)]) -> None:
        self.add_parent_node("expression")
        self.compile_term(token)

        tag, value = token = self.get_token()
        if tag == "symbol" and value in self.op_symbols:
            self.write_to_xml(token)
            self.token_idx += 1
            self.compile_term(self.get_token())
            if value == "*":
                print("!!! MULT SYMBOL: NEED TO CALL Math.mult() or smth like that !!!")
            elif value == "/":
                print("!!! DIV SYMBOL: NEED TO CALL Math.div() or smth like that !!!")
            else:
                VMWriter.perform_operation(value)

        self.pop_parent_node()

    
    def compile_term(self, token: (str, str)) -> None:
        self.add_parent_node("term")
        tag, value = token
        self.write_to_xml(token)

        if tag == "integerConstant":
            VMWriter.push(tag, value)
        elif tag == "identifier":
            result = self.symbol_table.find_symbol(value)
            VMWriter.push_variable(result)

        self.token_idx += 1

        if tag == "identifier":
            token = self.get_token()

            if token == ("symbol", "("):
                self.compile_expression(token, [("symbol", ")")])
                token = self.get_token()
                assert token == ("symbol", ")")
            elif token == ("symbol", "["):
                self.write_to_xml(token)
                self.token_idx += 1

                self.compile_expression(self.get_token(), [("symbol", "]")])
                
                token = self.get_token()
                assert token == ("symbol", "]")
                self.write_to_xml(token)
                self.token_idx += 1
            elif token == ("symbol", "."):
                while token != ("symbol", "("):
                    token = self.get_token()
                    self.write_to_xml(token)
                    self.token_idx += 1
                    
                self.compile_expression_list(self.get_token())
                token = self.get_token()
                assert token == ("symbol", ")")
                self.write_to_xml(token)
                self.token_idx += 1
        
        elif token == ("symbol", "("):
            self.compile_expression(self.get_token(), [("symbol", ")")])

            token = self.get_token()
            assert token == ("symbol", ")")
            self.write_to_xml(token)
            self.token_idx += 1

        elif tag == "symbol" and value in self.unary_op:
            self.compile_term(self.get_token())

        self.pop_parent_node()


    def compile(self) -> None:
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

        tree = ET.ElementTree(root)
        tree.write(self.output_filename)
        self.prettify_xml(self.output_filename)

        # TODO: remove
        for table in self.symbol_table.tables:
            print(table)


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