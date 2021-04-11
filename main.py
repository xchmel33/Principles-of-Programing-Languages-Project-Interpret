import sys
import os
from os import path
import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString  # extra library for checking xml version and encoding


# 10 - chybějící parametr skriptu (je-li třeba) nebo použití zakázané kombinace parametrů;
# 11 - chyba při otevírání vstupních souborů (např. neexistence, nedostatečné oprávnění);
# 12 - chyba při otevření výstupních souborů pro zápis (např. nedostatečné oprávnění, chyba při zápisu);
# 31 - chybný XML formát ve vstupním souboru (soubor není tzv. dobře formátovaný, angl. well-formed, viz [1]);
# 32 - neočekávaná struktura XML (např. element pro argument mimo element pro instrukci, instrukce s duplicitním pořadím nebo záporným pořadím) či lexikální nebo
#      syntaktická chyba textových elementů a atributů ve vstupním XML souboru (např. chybný lexém pro číselný nebo řetězcový literál, neznámý operační kód apod.).
# 52 - chyba při sémantických kontrolách vstupního kódu v IPPcode21 (např. použití nedefinovaného návěští, redefinice proměnné);
# 53 - běhová chyba interpretace – špatné typy operandů;
# 54 - běhová chyba interpretace – přístup k neexistující proměnné (rámec existuje);
# 55 - běhová chyba interpretace – rámec neexistuje (např. čtení z prázdného zásobníku rámců);
# 56 - běhová chyba interpretace – chybějící hodnota (v proměnné, na datovém zásobníku nebo v zásobníku volání);
# 57 - běhová chyba interpretace – špatná hodnota operandu (např. dělení nulou, špatná návratová hodnota instrukce EXIT);
# 58 - běhová chyba interpretace – chybná práce s řetězcem.
# 99 - interní chyba (neovlivněná vstupními soubory či parametry příkazové řádky; např. chyba alokace paměti).

class var:
    def __init__(self, name, value, type, frame):
        self.name = name
        self.value = value
        self.type = type
        self.frame = frame


class instr:
    def __init__(self, opcode):
        self.opcode = opcode
        self.args = []

    def add_argument(self, argumentType, argumentValue):
        self.args.append(arg(argumentType, argumentValue))


class arg:
    def __init__(self, argumentType, argumentValue):
        self.type = argumentType
        self.value = argumentValue


# functions checks if file exists and sufficient permisions for reading
def get_file(param):
    x = param.split("=")
    if path.isfile(x[1]) and os.access(x[1], os.R_OK):
        return x[1]
    else:
        exit(11)


# function checks if string represents an integer
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def symb(type, value):
    if type == "var":
        if value[0:3] == "GF@" and value[3:] in GF.keys():
            if GF[value[3:]].value == "none":
                exit(56)    # missing value in variable
            else:
                return value
        else:
            exit(54)    # variable doesn't exist
    elif type == "int" and is_int(value):
        return value
    elif type == "bool" and value == "true" or value == "false":
        return value
    elif type == "nil" or type == "string":
        return value
    else:
        exit(2)     # invalid type


if __name__ == '__main__':

    # Process arguments
    if sys.argv[1] == "--help":

        # Edit
        print("Usage: interpret.py [--help, --source=file, --input=file]\n"
              "IPPcode21 interpreter reads source file xml code representation\n"
              "and input file with inputs of the program, checks for any semantic\n"
              "or other errors and ")

        # No more arguments after help permitted
        if len(sys.argv) > 2:
            exit(10)
        else:
            exit(0)

    # --input or --input --source parameters
    elif sys.argv[1][0:8] == "--input=":
        inputFile = get_file(sys.argv[1])
        if len(sys.argv) > 2:
            if sys.argv[2][0:9] == "--source=":
                sourceFile = get_file(sys.argv[2])
            else:
                exit(10)

    # --source or --source --input parameters
    elif sys.argv[1][0:9] == "--source=":
        sourceFile = get_file(sys.argv[1])
        if len(sys.argv) > 2:
            if sys.argv[2][0:8] == "--input=":
                inputFile = get_file(sys.argv[2])
            else:
                exit(10)

    # Error: at least one parameter is required
    else:
        exit(10)

    # stdin input in case of missing arguments
    try:
        sourceFile
    except NameError:
        sourceFile = sys.stdin
    try:
        inputFile
    except NameError:
        inputFile = sys.stdin

    # XML well-formed ?

    # XML program representation parsing
    try:
        XMLCode = ET.parse(sourceFile)
    except SyntaxError:
        exit(31)    # XML is not well-formed
    grandparent = XMLCode.getroot()
    if grandparent.tag != "program" or 'language' not in grandparent.attrib.keys() or grandparent.attrib['language'] != "IPPcode21":
        exit(32)    # invalid root tag or program language

    # instructions parsing
    instructions = [0 for x in range(100)]  # array of instructions for sorting by instruction order
    for parent in grandparent:
        if parent.tag != "instruction" or 'order' not in parent.attrib.keys() or not is_int(parent.attrib['order']) or 'opcode' not in parent.attrib.keys():
            exit(32)    # invalid instruction name or missing order or opcode
        else:

            # create instruction at index defined by order
            index = int(parent.attrib['order'])
            if instructions[index] != 0:
                exit(32)    # duplicate instruction order
            else:
                instructions[index] = instr(parent.attrib['opcode'])

            # argument parsing
            for child in parent:
                if child.tag[0:3] != "arg" or 'type' not in child.attrib.keys():
                    exit(32)    # invalid argument name or missing type
                else:
                    instructions[index].add_argument(child.attrib['type'], child.text)

    # remove empty instructions
    instructions = list(filter((0).__ne__, instructions))

    # print
    for instruction in instructions:
        print(instruction.opcode, end=" ")
        for argument in instruction.args:
            print(argument.type + " " + argument.value)

    # IPPcode21 interpreter
    GF = {}
    LF = {} # implement as stack
    TF = {}
    for inst in instructions:
        name = inst.opcode.upper()
        if name == "MOVE":
            exit(0)
        elif name == "CREATEFRAME":
            exit(0)
        elif name == "PUSHFRAME":
            exit(0)
        elif name == "POPFRAME":
            exit(0)
        elif name == "DEFVAR":
            if inst.args[0].type != "var":
                exit(32)    # type must be var ?
            else:
                name = inst.args[0].value[3:]
                frame = inst.args[0].value[0:3]
                variable = var(name, "none", "undefined", frame)
            if frame == "GF@":
                GF[name] = variable
            elif frame == "LF@":
                LF[name] = variable
            elif frame == "TF@":
                TF[name] = variable
            else:
                exit(1)     # invalid frame
        elif name == "CALL":
            exit(0)
        elif name == "RETURN":
            exit(0)
        elif name == "PUSHS":
            exit(0)
        elif name == "POPS":
            exit(0)
        elif name == "ADD":
            exit(0)
        elif name == "SUB":
            exit(0)
        elif name == "MUL":
            exit(0)
        elif name == "DIV":
            exit(0)
        elif name == "IDIV":
            exit(0)
        elif name == "LT":
            exit(0)
        elif name == "GT":
            exit(0)
        elif name == "EQ":
            exit(0)
        elif name == "AND":
            exit(0)
        elif name == "OR":
            exit(0)
        elif name == "NOT":
            exit(0)
        elif name == "INT2CHAR":
            exit(0)
        elif name == "STRI2INT":
            exit(0)
        elif name == "READ":
            exit(0)
        elif name == "WRITE":
            if len(inst.args) != 1:
                exit(32)    # invalid number of arguments
            else:
                print(symb(inst.args[0].type, inst.args[0].value))
        elif name == "CONCAT":
            exit(0)
        elif name == "STRLEN":
            exit(0)
        elif name == "GETCHAR":
            exit(0)
        elif name == "SETCHAR":
            exit(0)
        elif name == "TYPE":
            exit(0)
        elif name == "LABEL":
            exit(0)
        elif name == "JUMP":
            exit(0)
        elif name == "JUMPIFEQ":
            exit(0)
        elif name == "JUMPIFNEQ":
            exit(0)
        elif name == "EXIT":
            exit(0)
        elif name == "DPRINT":
            exit(0)
        elif name == "BREAK":
            exit(0)
        else:
            exit(32)    # invalid instruction opcode
