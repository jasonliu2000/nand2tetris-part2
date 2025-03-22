import sys
from pathlib import Path
from typing import List

class Translate:

    valid_cmds = {
        "add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not",  # arithmetic/logical
        "pop", "push",                                              # memory access
        "label", "goto", "if-goto",                                 # branching
        "function", "call", "return",                               # function
    }

    valid_segments = {
        "local", "argument", "this", "that", "constant", "static", "temp", "pointer"
    }

    saved_pointers = ["@LCL", "@ARG", "@THIS", "@THAT"]

    R1 = "@R13"
    R2 = "@R14"
    R3 = "@R15"

    op_count = 0
    current_caller = ""
    caller_count = {}


    def __init__(self, output_filename: str = "", is_dir: bool = False):
        # delete output file if it already exists
        output_file = Path(output_filename)
        if output_file.is_file():
            output_file.unlink()

        self.output_file = output_filename

        if is_dir:
            self.bootstrap()
    

    def write(self, code: str) -> None:
        print(code, file=self.file_stream)


    def bootstrap(self) -> None:
        with open(f'{self.output_file}', "a") as file_stream:
            self.file_stream = file_stream
            self.write("@256")
            self.write("D=A")
            self.write("@SP")
            self.write("M=D")
            self.current_caller = "Bootstrap"
            self.call_function("Sys.init", 0)


    def translate(self, input_file: str) -> None:
        self.ref = input_file.rsplit("/", 1)[-1][:-3]

        with open(input_file, "r") as file:
            contents = file.read()

        lines = contents.splitlines()

        with open(f'{self.output_file}', "a") as file_stream:
            self.file_stream = file_stream

            for line in lines:
                stripped_line = line.partition("//")[0].strip()
                
                if not stripped_line:
                    continue

                parsed_components = self.parse(stripped_line)
                self.write_to_asm(parsed_components)
    

    def parse(self, line: str) -> List:
        components = line.split()
        cmd = components[0]

        if cmd not in self.valid_cmds:
            print(f"Error: '{cmd}' is not a valid command.")
            sys.exit(1)

        if cmd in ["pop", "push"]:
            _, segment, val = components

            if segment not in self.valid_segments:
                print(f"Error: '{segment}' is not a valid memory segment.")
                sys.exit(1)
            
            if not val.isdigit:
                print(f"Error: '{val}' is an invalid value.")
                sys.exit(1)
            
            components[2] = int(val)
        
        return components
    

    def pop(self) -> None:
        # decrement stack pointer first
        self.write("@SP")
        self.write("M=M-1")
        self.write("A=M")
        
    
    def pop_and_store(self, register=None, index=None) -> None:

        if register == "pointer":
            pointer = "THIS" if index == 0 else "THAT"
            self.pop()
            self.write("D=M")
            self.write(f"@{pointer}")
            self.write("M=D")
            return

        elif register == "constant":
            self.pop()
            self.write("D=M")
            self.write(f"@{index}")
            self.write("M=D")

        elif register == "static":
            self.pop()
            self.write("D=M")
            self.write(f"@{self.ref}.{index}")
            self.write("M=D")

        elif register == "temp":
            # store index in R13
            self.write(f"@{index}")
            self.write("D=A")
            self.write("@5")
            self.write("D=D+A")
            self.write(self.R1)
            self.write("M=D")
            
            # pop
            self.pop()
            self.write("D=M")

            # store popped value into index that was stored in R13
            self.write(self.R1)
            self.write("A=M")
            self.write("M=D")

        else:
            self.write(f"@{index}")
            self.write("D=A")
            if register == "local":
                self.write("@LCL")
            elif register == "argument":
                self.write("@ARG")
            elif register == "this":
                self.write("@THIS")
            elif register == "that":
                self.write("@THAT")

            # store index in R13
            self.write("D=D+M")
            self.write(self.R1)
            self.write("M=D")
            
            # pop
            self.pop()
            self.write("D=M")

            # store popped value into index that was stored in Register 1
            self.write(self.R1)
            self.write("A=M")
            self.write("M=D")

    
    def get_and_push(self, register=None, index=None) -> None:

        if register == "pointer":
            pointer = "THIS" if index == 0 else "THAT"
            self.write(f"@{pointer}")
            self.write("D=M")

        elif register == "static":
            self.write(f"@{self.ref}.{index}")
            self.write("D=M")

        elif register == "constant":
            self.write(f"@{index}")
            self.write("D=A")

        elif register == "temp":
            self.write(f"@{index}")
            self.write("D=A")
            self.write("@5")
            self.write("A=D+A")
            self.write("D=M")

        else:
            self.write(f"@{index}")
            self.write("D=A")
            if register == "local":
                self.write("@LCL")
            elif register == "argument":
                self.write("@ARG")
            elif register == "this":
                self.write("@THIS")
            elif register == "that":
                self.write("@THAT")

            self.write("A=D+M")
            self.write("D=M")

        self.push()
    

    def push(self) -> None:
        self.write("@SP")
        self.write("A=M")
        self.write("M=D")

        # increment stack pointer
        self.write("@SP")
        self.write("M=M+1")
    
    def perform_arithmetic(self, cmd: str) -> None:
        self.pop()
        self.write("D=M")

        if cmd in ["neg", "not"]:
            if cmd == "neg":
                self.write("D=-D")
            else:
                self.write("D=!D")

            # get stack pointer
            self.write("@SP")
            self.write("A=M")

            # store D in memory of stack pointer
            self.write("M=D")

            # increment stack pointer
            self.write("@SP")
            self.write("M=M+1")
            return

        # pop second value
        self.pop()

        # perform op and store result in D
        if cmd == "add":
            self.write("D=D+M")
        elif cmd == "sub":
            self.write("D=M-D")
        elif cmd == "and":
            self.write("D=D&M")
        elif cmd == "or":
            self.write("D=D|M")
        else:
            self.write("D=M-D")
            self.write(f"@SET_TRUE{self.op_count}")

            if cmd == "eq":
                self.write("D;JEQ")
            elif cmd == "gt":
                self.write("D;JGT")
            elif cmd == "lt":
                self.write("D;JLT")

            self.write("D=0") # set D to false
            self.write(f"@END{self.op_count}")
            self.write("0;JMP")

            self.write(f"(SET_TRUE{self.op_count})")
            self.write("D=-1") # set D to true (-1, aka 1111111111111111)

            self.write(f"(END{self.op_count})")
            self.op_count += 1

        self.push()
    

    def get_full_label(self, label: str) -> str:
        prefix = f'{self.current_caller}$' if self.current_caller else ""
        return prefix + label

    
    def call_function(self, name: str, n_args: int) -> None:
        # set return address
        caller = self.current_caller
        if caller == "Bootstrap":
            return_address = caller + "$ret"
        else:
            self.caller_count[caller] = self.caller_count.setdefault(caller, 0) + 1
            return_address = f'{caller}$ret.{self.caller_count[caller]}'

        # push return address
        self.write(f'@{return_address}')
        self.write("D=A")
        self.push()

        for pointer in self.saved_pointers:
            self.write(pointer)
            self.write("D=M")
            self.push()
        
        # ARG = SP - 5 - nArgs
        self.write(f'@{5 + int(n_args)}')
        self.write("D=A")
        self.write("@SP")
        self.write("D=M-D")
        self.write("@ARG")
        self.write("M=D")

        # LCL = SP
        self.write("@SP")
        self.write("D=M")
        self.write("@LCL")
        self.write("M=D")

        # goto function
        self.write(f'@{name}')
        self.write("0;JMP")

        # add return address label
        self.write(f'({return_address})')
    

    def return_function(self) -> None:
        # save LCL to Register 1
        self.write("@LCL")
        self.write("D=M")
        self.write(f'{self.R1}')
        self.write("M=D")
        
        # store return address to Register 2
        self.write("@5")
        self.write("D=D-A")
        self.write("A=D")
        self.write("D=M")
        self.write(f'{self.R2}')
        self.write("M=D")

        # pop and store at index ARG
        self.pop()
        self.write("D=M")
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")

        # SP = ARG + 1
        self.write("@ARG")
        self.write("D=M+1")
        self.write("@SP")
        self.write("M=D")

        # restore THAT, THIS, ARG, LCL
        pc = len(self.saved_pointers)
        for i in range(1, pc+1):
            self.write(f'{self.R1}')
            self.write("D=M")
            self.write(f'@{i}')
            self.write("D=D-A")
            self.write("A=D")
            self.write("D=M") # D = saved address of pointer
            self.write(self.saved_pointers[pc-i])
            self.write("M=D")
        
        # goto return address
        self.write(f'{self.R2}')
        self.write("D=M")
        self.write("A=D")
        self.write("0;JMP")

    
    def write_to_asm(self, components: List[str]) -> None:
        cmd = components[0]

        if len(components) == 1 and cmd != "return":
            self.perform_arithmetic(cmd)
        elif cmd == "return":
            self.return_function()
        elif cmd == "push":
            self.get_and_push(register=components[1], index=components[2])
        elif cmd == "pop":
            self.pop_and_store(register=components[1], index=components[2])
        elif cmd == "label":
            self.write(f'({self.get_full_label(components[1])})')
        elif cmd == "if-goto":
            self.pop()
            self.write("D=M")
            self.write(f'@{self.get_full_label(components[1])}')
            self.write("D;JNE")
        elif cmd == "goto":
            self.write(f'@{self.get_full_label(components[1])}')
            self.write("0;JMP")
        elif cmd == "function":
            name, n_vars = components[1:]
            self.write(f'({name})')
            for _ in range(int(n_vars)):
                self.write("@0")
                self.write("D=A")
                self.push()
            self.current_caller = name
        elif cmd == "call":
            function_name, n_args = components[1:]
            self.call_function(function_name, int(n_args))
        else:
            print(f"Error: the command '{segment}' has not been implemented yet.")
            sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python VMTranslator.py [filename|directory]")
        sys.exit(1)

    main_arg = sys.argv[1]

    if main_arg.endswith(".vm"):
        input_filename = main_arg
        if not Path(input_filename).is_file():
            print(f"Error: File '{input_filename}' not found.")
            sys.exit(1)

        output_filename = input_filename[:-3] + ".asm"
        Translate(output_filename).translate(input_filename)
            
    elif Path(main_arg).is_dir():
        directory = main_arg
        filename = directory.rsplit("/", 1)[-1] + ".asm"
        output_filename = directory + "/" + filename
        translator = Translate(output_filename, True)

        for file in Path(directory).iterdir():
            if file.name.endswith(".vm"):
                input_filename = f'{directory}/{file.name}'
                translator.translate(input_filename)
                
    else:
        print(f"Error: Input must be a either a filename with .vm extension or a directory")
        sys.exit(1)


if __name__ == "__main__":
    main()