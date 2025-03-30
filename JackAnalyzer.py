import sys
from pathlib import Path

from CompilationEngine import compileStatements
from JackTokenizer import tokenize

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackAnalyzer.py [filename|directory]")
        sys.exit(1)

    main_arg = sys.argv[1]

    if main_arg.endswith(".jack"):
        input_filename = main_arg
        if not Path(input_filename).is_file():
            print(f"Error: File '{input_filename}' not found.")
            sys.exit(1)

        tokenized_file = tokenize(input_filename)
        compileStatements(tokenized_file)
            
    elif Path(main_arg).is_dir():
        directory = main_arg
        for file in Path(directory).iterdir():
            if file.name.endswith(".jack"):
                input_filename = f'{directory}/{file.name}'
                tokenized_file = tokenize(input_filename)
                compileStatements(tokenized_file)
                
    else:
        print(f"Error: Input must be a either a filename with .jack extension or a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()