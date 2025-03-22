import sys
from typing import List
from typing import TextIO

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

    label_idx = {}

    R1 = "@R13"
    R2 = "@R14"
    R3 = "@R15"

    op_count = 0

    def __init__(self, ref):
        self.ref = ref
        self.output_file = f"{ref}.asm"
    

    def translate(self, contents: str):
        lines = contents.splitlines()

        with open(f'{self.output_file}', "w") as file_stream:
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
    

    def write(self, code: str) -> None:
        print(code, file=self.file_stream)
    

    def pop(self) -> None:
        # decrement stack pointer first
        self.write("@SP")
        self.write("M=M-1")

        self.write("@SP")
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

    
    def write_to_asm(self, components: List[str]) -> None:
        cmd = components[0]

        if len(components) == 1: # TODO: make this if check more strict
            self.perform_arithmetic(cmd)
        elif cmd == "push":
            self.get_and_push(register=components[1], index=components[2])
        elif cmd == "pop":
            self.pop_and_store(register=components[1], index=components[2])
        elif cmd == "label":
            self.write(f'({components[1]})')
        elif cmd == "if-goto":
            self.pop()
            self.write("D=M")
            self.write(f'@{components[1]}')
            self.write("D;JNE")
        else:
            print(f"Error: the command '{segment}' has not been implemented yet.")
            sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python translate.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    if not filename.endswith(".vm"):
        print(f"Error: File '{filename}' does not have a .vm extension.")
        sys.exit(1)

    try:
        with open(filename, "r") as file:
            contents = file.read()
            ref = filename[:-3]
            Translate(ref).translate(contents)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()