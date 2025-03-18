import sys
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
            for line in lines:
                stripped_line = line.partition("//")[0].strip()
                
                if not stripped_line:
                    continue

                parsed_components = self.parse(stripped_line)
                self.write_assembly(parsed_components, file_stream)
    

    def parse(self, line: str) -> list:
        components = line.split()
        if components[0] not in self.valid_cmds:
            print(f"Error: '{components[0]}' is not a valid command.")
            sys.exit(1)

        if len(components) > 1:
            _, segment, val = components

            if segment not in self.valid_segments:
                print(f"Error: '{segment}' is not a valid memory segment.")
                sys.exit(1)
            
            if not val.isdigit:
                print(f"Error: '{val}' is an invalid value.")
                sys.exit(1)
            
            components[2] = int(val)
        
        return components
    

    def pop(self, file: TextIO, register: str) -> None:
        print("@SP", file=file)
        print("M=M-1", file=file)
        print("@SP", file=file)
        print("A=M", file=file)
        print("D=M", file=file)
        print(register, file=file)
        print("M=D", file=file)
        
    
    def pop_and_store_in_register(self, file: TextIO, register=None, index=None) -> None:
        temp_popped_val = self.R1
        self.pop(file, register=temp_popped_val)

        if register == "pointer":
            pointer = "THIS" if index == 0 else "THAT"
            print(temp_popped_val, file=file)
            print("D=M", file=file)
            print(f"@{pointer}", file=file)
            print("M=D", file=file)
            return

        elif register == "constant":
            print(f"@{index}", file=file)
            print("D=A", file=file)
        elif register == "static":
            print(f"@{self.ref}.{index}", file=file)
            print("D=A", file=file)
        elif register == "temp":
            print(f"@{index}", file=file)
            print("D=A", file=file)
            print("@5", file=file)
            print("D=D+A", file=file)
        else:
            print(f"@{index}", file=file)
            print("D=A", file=file)
            if register == "local":
                print("@LCL", file=file)
            elif register == "argument":
                print("@ARG", file=file)
            elif register == "this":
                print("@THIS", file=file)
            elif register == "that":
                print("@THAT", file=file)

            print("D=D+M", file=file)
        
        print(self.R2, file=file)
        print("M=D", file=file) # temporarily store target index in Register 2
        print(temp_popped_val, file=file)
        print("D=M", file=file) # now transfer popped value to D
        print(self.R2, file=file)
        print("A=M", file=file)
        print("M=D", file=file) # set register[index] to popped value

    
    def get_val_from_register_and_push(self, file: TextIO, register=None, index=None) -> None:
        if register == "pointer":
            pointer = "THIS" if index == 0 else "THAT"
            print(f"@{pointer}", file=file)
            print("D=M", file=file)
        elif register == "static":
            print(f"@{self.ref}.{index}", file=file)
            print("D=M", file=file)
        elif register == "constant":
            print(f"@{index}", file=file)
            print("D=A", file=file)
        elif register == "temp":
            print(f"@{index}", file=file)
            print("D=A", file=file)
            print("@5", file=file)
            print("A=D+A", file=file)
            print("D=M", file=file)
        else:
            print(f"@{index}", file=file)
            print("D=A", file=file)
            if register == "local":
                print("@LCL", file=file)
            elif register == "argument":
                print("@ARG", file=file)
            elif register == "this":
                print("@THIS", file=file)
            elif register == "that":
                print("@THAT", file=file)

            print("A=D+M", file=file)
            print("D=M", file=file)

        temp_val_to_push = self.R1
        print(temp_val_to_push, file=file)
        print("M=D", file=file) # store value from register[index] to a temp register

        self.push(file, temp_val_to_push)
    

    def push(self, file: TextIO, register: str) -> None:
        # first store the val we want to push to D
        print(register, file=file)
        print("D=M", file=file)

        # get stack pointer
        print("@SP", file=file)
        print("A=M", file=file)

        # store D in memory of stack pointer
        print("M=D", file=file)

        # increment stack pointer
        print("@SP", file=file)
        print("M=M+1", file=file)
    
    def perform_arithmetic(self, cmd: str, file: TextIO) -> None:
        # pop element and store in Register 1
        self.pop(file, register=self.R1)

        if cmd in ["neg", "not"]:
            print(self.R1, file=file)
            if cmd == "neg":
                print("D=-M", file=file)
            else:
                print("D=!M", file=file)
            print(self.R3, file=file)
            print("M=D", file=file)
            self.push(file, register=self.R3)
            return

        # pop next element and store in Register 2
        self.pop(file, register=self.R2)
        
        print(self.R1, file=file)
        print("D=M", file=file)
        print(self.R2, file=file)

        # perform op and store result in D
        if cmd == "add":
            print("D=D+M", file=file)
        elif cmd == "sub":
            print("D=M-D", file=file)
        elif cmd == "and":
            print("D=D&M", file=file)
        elif cmd == "or":
            print("D=D|M", file=file)
        else:
            if cmd == "eq":
                print("D=M-D", file=file)
                print(f"@SET_TRUE{self.op_count}", file=file)
                print("D;JEQ", file=file)
            elif cmd == "gt":
                print("D=M-D", file=file)
                print(f"@SET_TRUE{self.op_count}", file=file)
                print("D;JGT", file=file)
            elif cmd == "lt":
                print("D=M-D", file=file)
                print(f"@SET_TRUE{self.op_count}", file=file)
                print("D;JLT", file=file)

            print("D=0", file=file)
            print(f"@END{self.op_count}", file=file)
            print("0;JMP", file=file)

            print(f"(SET_TRUE{self.op_count})", file=file)
            print("D=-1", file=file) # set D equal to true (-1, aka 1111111111111111)

            print(f"(END{self.op_count})", file=file)
            self.op_count += 1

        # store result from D into Register 3
        print(self.R3, file=file)
        print("M=D", file=file)

        self.push(file, register=self.R3)

    
    def write_assembly(self, components: list[str], file: TextIO) -> None:
        cmd = components[0]

        if len(components) == 1:
            self.perform_arithmetic(cmd, file)
        elif cmd == "push":
            self.get_val_from_register_and_push(file=file, register=components[1], index=components[2])
        elif cmd == "pop":
            self.pop_and_store_in_register(file=file, register=components[1], index=components[2])
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