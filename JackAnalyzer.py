import sys
import re

from typing import List
from pathlib import Path

def remove_inline_comments(line: str) -> str:
    n = len(line)
    for i in range(n):
        if i+1 < n and line[i:i+2] == "//":
            return line[:i].strip()

    return line


def remove_doc_comments(code: str) -> str:
    i, n = 0, len(code)
    is_comment = False
    result = ""

    while i < n:
        if not is_comment and i+2 < n and code[i:i+3] == "/**":
            is_comment = True
        elif i+1 < n and code[i:i+2] == "*/":
            is_comment = False
            i += 1
        elif not is_comment:
            result += code[i]

        i += 1

    return result


def remove_comments(filename: str) -> str:
    with open(filename, "r") as file:
        lines = file.read().splitlines()
        cleaned_code = ""

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("//"):
                continue

            cleaned_code += remove_inline_comments(stripped_line)
        
        # print(cleaned_code)
        cleaned_code = remove_doc_comments(cleaned_code)
        # print(cleaned_code)
        return cleaned_code


def write(file_stream, type: str, value: str = "") -> None:
    if value:
        print(f"<{type}> {value} </{type}>", file=file_stream)
    else:
        print(f"<{type}>", file=file_stream)


def tokenize(filename: str) -> None:
    cleaned_file = remove_comments(filename)

    output_filename = filename[:-5] + "T" + ".xml"

    # delete output file if it already exists
    file = Path(output_filename)
    if file.is_file():
        file.unlink()

    symbols = {
        "{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"
    }

    keywords = {
        "class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"
    }

    with open(filename, "a") as file_stream:
        write(file_stream, "tokens")
        
        for phrase in phrases:
            i = 0
            while i < len(phrase):
                current_val = ""

                while i < len(phrase) and phrase[i].isdigit():
                    current_val += phrase[i]
                    i += 1
                
                if current_val:
                    write(file_stream, "integerConstant", current_val)
                    current_val = ""
                
                if i < len(phrase) and phrase[i] == '"':
                    i += 1
                    while i < len(phrase) and phrase[i] != '"':
                        current_val += phrase[i]
                        i += 1

                    write(file_stream, "stringConstant", current_val)
                    current_val = ""


                while i < len(phrase) and phrase[i] not in symbols:
                    current_val += phrase[i]
                    i += 1

                if current_val in keywords:
                    write(file_stream, "keyword", current_val)
                elif current_val:
                    write(file_stream, "identifier", current_val)
                    current_val = ""
                
                if i < len(phrase) and phrase[i] in symbols:
                    write(file_stream, "symbol", phrase[i])
                    i += 1

        write(file_stream, "/tokens")


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

        tokenize(input_filename)
            
    elif Path(main_arg).is_dir():
        directory = main_arg
        for file in Path(directory).iterdir():
            if file.name.endswith(".jack"):
                input_filename = f'{directory}/{file.name}'
                tokenize(input_filename)
                
    else:
        print(f"Error: Input must be a either a filename with .jack extension or a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()