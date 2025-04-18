import sys
from pathlib import Path
from typing import List

symbols = {
    "{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"
}

keywords = {
    "class", "constructor", "function", "method", "field", "static", "var", "int", "char", "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"
}

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
        
        cleaned_code = remove_doc_comments(cleaned_code)
        return cleaned_code


def write(file_stream, type: str, value: str = "") -> None:
    if value:
        print(f"<{type}> {value} </{type}>", file=file_stream)
    else:
        print(f"<{type}>", file=file_stream)


def tokenize(filename: str) -> str:
    output_filename = filename[:-5] + "T" + ".xml"

    # delete output file if it already exists
    file = Path(output_filename)
    if file.is_file():
        file.unlink()

    contents = remove_comments(filename)

    with open(output_filename, "a") as file_stream:
        write(file_stream, "tokens")
        
        i, n = 0, len(contents)
        while i < n:
            char = contents[i]

            if char == '"':
                i += 1
                j = contents.find('"', i)
                if j == -1:
                    print("Syntax error: unterminated string literal")
                    sys.exit(1)

                write(file_stream, "stringConstant", contents[i:j])
                i = j + 1 # add 1 to skip the trailing '"'
                continue

            if char.isdigit():
                j = i
                while j < n and contents[j].isdigit():
                    j += 1

                write(file_stream, "integerConstant", contents[i:j])
                i = j
                continue

            # this is to check if a string is a class or identifier. An identifier can contain digits, 
            # but it cannot start with a digit (hence isalpha() check in if-statement and isalnum() check in while-loop)
            if char.isalpha() or char == "_":
                j = i
                while j < n and (contents[j].isalnum() or char == "_"):
                    j += 1
                
                value = contents[i:j]
                if value in keywords:
                    write(file_stream, "keyword", value)
                else:
                    write(file_stream, "identifier", value)
                
                i = j
                continue
                
            if char in symbols:
                encoded = char

                if char == "&":
                    encoded = "&amp;"
                elif char == "<":
                    encoded = "&lt;"
                elif char == ">":
                    encoded = "&gt;"
                
                write(file_stream, "symbol", encoded)
            
            i += 1

        write(file_stream, "/tokens")

    return output_filename
