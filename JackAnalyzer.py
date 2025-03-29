import sys
import re

from typing import List
from pathlib import Path

def phrasify(code: str) -> List[str]:
    initial_phrases = code.split()
    result = []
    
    for phrase in initial_phrases:
        if "//" in phrase:
            end_idx = phrase.find("//")
            fragment = phrase[:end_idx].strip()
            
            if len(fragment) > 0:
                phrases.append(fragment)

            break

        result.append(phrase)

    return result


def strip_doc_comments(phrases: List[str]) -> List[str]:
    phrase_idx, total_phrases = 0, len(phrases)
    is_comment = False
    result = []

    while phrase_idx < total_phrases:
        while phrase_idx < total_phrases and is_comment:
            phrase = phrases[phrase_idx]
            if "*/" in phrase:
                end_idx = phrase.find("*/") + len("*/")
                valid_phrase = phrase[end_idx:]

                if valid_phrase:
                    result.append(valid_phrase)

                is_comment = False
            
            phrase_idx += 1

        if phrase_idx == total_phrases:
            break

        phrase = phrases[phrase_idx]

        if "/**" in phrase:
            start_idx = phrase.find("/**")
            valid_phrase = phrase[:start_idx]

            if valid_phrase:
                result.append(valid_phrase)

            is_comment = True
        else:
            result.append(phrase)

        phrase_idx += 1
    
    return result


def clean_and_phrasify(input_filename: str) -> List[str]:
    with open(input_filename, "r") as file:
        lines = file.read().splitlines()
        phrases = []

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("//"):
                continue

            phrases += phrasify(stripped_line)
        
        # print(phrases)
        cleaned_phrases = strip_doc_comments(phrases)
        # print(cleaned_phrases)
        return cleaned_phrases


def write(file_stream, type: str, value: str = "") -> None:
    if value:
        print(f"<{type}> {value} </{type}>", file=file_stream)
    else:
        print(f"<{type}>", file=file_stream)


def tokenize(filename: str, phrases: List[str]) -> None:
    # delete output file if it already exists
    file = Path(filename)
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

        phrases = clean_and_phrasify(input_filename)

        output_filename = input_filename[:-5] + "T" + ".xml"
        tokenize(output_filename, phrases)
            
    elif Path(main_arg).is_dir():
        directory = main_arg
        for file in Path(directory).iterdir():
            if file.name.endswith(".jack"):
                input_filename = f'{directory}/{file.name}'
                phrases = clean_and_phrasify(input_filename)

                output_filename = input_filename[:-5] + "T" + ".xml"
                tokenize(output_filename, phrases)
                
    else:
        print(f"Error: Input must be a either a filename with .jack extension or a directory")
        sys.exit(1)

if __name__ == "__main__":
    main()