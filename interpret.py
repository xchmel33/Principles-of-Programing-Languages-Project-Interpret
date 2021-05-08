import sys
import os
from os import path
import xml.etree.ElementTree as ET


# class for storing variables
class var:
    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type


# class for storing instructions
class instr:
    def __init__(self, opcode):
        self.opcode = opcode
        self.args = []

    def add_argument(self, argumentType, argumentValue):
        self.args.append(arg(argumentType, argumentValue))


# class for storing arguments
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


# symb -> constant or variable
def symb_check(symb):

    # variable definition check
    if symb.type == "var":
        frame = symb.value[0:3]
        name = symb.value[3:]
        if frame == "GF@" and name in GF.keys():
            if GF[name].value == "none":
                exit(56)  # missing value in variable
            else:
                s_result = arg(GF[name].type, GF[name].value)
                return s_result
        elif frame == "LF@":
            if LFTop == -1:
                exit(55)
            if name in LF[LFTop].keys():
                if LF[LFTop][name].value == "none":
                    exit(56)  # missing value in variable
                else:
                    s_result = arg(LF[LFTop][name].type, LF[LFTop][name].value)
                    return s_result
            else:
                exit(54)
        elif frame == "TF@":
            try:
                if name in TF.keys():
                    if TF[name].value == "none":
                        exit(56)  # missing value in variable
                    else:
                        s_result = arg(TF[name].type, TF[name].value)
                        return s_result
                else:
                    exit(54)
            except NameError:
                exit(55)
        else:
            exit(54)  # undefined variable

    # matching types check
    elif symb.type == "int" and is_int(symb.value):
        symb.value = int(symb.value)
        return symb
    elif symb.type == "bool" and (symb.value == "true" or symb.value == "false"):
        return symb
    elif symb.type == "nil" or symb.type == "string":
        return symb
    else:
        exit(32)  # invalid type

# function checks if variable is defined and stores value inside it
def assign_to_var(variable, value):
    frame = variable.value[0:3]
    name = variable.value[3:]

    if frame == "GF@" and name in GF.keys():
        GF[name].value = value.value
        GF[name].type = value.type

    elif frame == "LF@":
        if LFTop == -1:
            exit(55)
        if name in LF[LFTop].keys():
            LF[LFTop][name].value = value.value
            LF[LFTop][name].type = value.type
        else:
            exit(54)

    elif frame == "TF@":
        try:
            if name in TF.keys():
                TF[name].value = value.value
                TF[name].type = value.type
            else:
                exit(54)
        except NameError:
            exit(55)

    else:
        exit(54)  # undefined variable

# convert decimal equivalent to char
def replace_dec(string):
    i = 0
    for c in string:
        try:
            if c == '\\' and is_int(string[i + 1]) and is_int(string[i + 2:i + 3]):
                if string[i + 1] == '0':
                    dec = chr(int(string[i + 2:i + 4]))
                else:
                    dec = chr(int(string[i + 1:i + 4]))
                string = string.replace(string[i:i + 4], dec)
        except IndexError:
            break
        i = i + 1
    return string

# main
if __name__ == '__main__':

    if len(sys.argv) < 2:
        exit(10)

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


    # XML program representation parsing
    try:
        XMLCode = ET.parse(sourceFile)
    except SyntaxError:
        exit(31)  # XML is not well-formed
    grandparent = XMLCode.getroot()
    if grandparent.tag != "program" or 'language' not in grandparent.attrib.keys() or grandparent.attrib[
        'language'] != "IPPcode21":
        exit(32)  # invalid root tag or program language

    # instructions parsing
    instructions = [0 for x in range(100)]  # array of instructions for sorting by instruction order
    for parent in grandparent:
        if parent.tag != "instruction" or 'order' not in parent.attrib.keys() or not is_int(
                parent.attrib['order']) or 'opcode' not in parent.attrib.keys():
            exit(32)  # invalid instruction name or missing order or opcode
        else:

            # create instruction at index defined by order
            index = int(parent.attrib['order'])

            # negative order
            if index < 1:
                exit(32)

            if instructions[index] != 0:
                exit(32)  # duplicate instruction order
            else:
                instructions[index] = instr(parent.attrib['opcode'])

            # argument parsing
            a = [0 for x in range(3)]
            argIndex = 0
            for child in parent:
                if child.tag[0:3] != "arg" or 'type' not in child.attrib.keys():
                    exit(32)  # invalid argument name or missing type
                else:

                    # empty string in argument
                    if child.text is None:
                        if child.attrib['type'] == "string":
                            child.text = ""
                        elif child.attrib['type'] == "bool":
                            child.text = "false"
                        else:
                            exit(32)

                    # convert decimal equivalent to char
                    else:
                        child.text = replace_dec(child.text)

                    # sort argmuents
                    argIndex = int(child.tag[3])
                    a[argIndex - 1] = arg(child.attrib['type'], child.text)

            # add sorted arguments
            i = 0
            for x in a:
                if x != 0:
                    instructions[index].add_argument(x.type, x.value)

                # check for missing arguments
                if i > 0 and a[i - 1] == 0 and a[i] != 0:
                    exit(32)
                i = i + 1

    # remove empty instructions
    instructions = list(filter((0).__ne__, instructions))


    # define labels before interpretation
    i = 0
    labels = {}
    while i != len(instructions):

        inst = instructions[i]
        name = inst.opcode.upper()
        argCount = len(inst.args)

        if name == "LABEL":
            if argCount != 1:
                exit(32)

            if inst.args[0].type != "label":
                exit(53)

            if inst.args[0].value in labels.keys():
                exit(52)

            labels[inst.args[0].value] = i

        i = i + 1

    # IPPcode21 interpreter variables
    GF = {}
    LF = []
    LFTop = -1
    dataStack = []
    dataStackTop = -1
    callStack = []
    callStackTop = -1
    instCount = 0
    i = 0
    x = 0
    try:
        f = open(inputFile, "r")
    except TypeError:
        f = sys.stdin
    output = ""

    # IPPcode21 interpreter instructions
    while i != len(instructions):

        inst = instructions[i]
        name = inst.opcode.upper()
        argCount = len(inst.args)

        debug = 0
        if debug:
            print(inst.opcode, end=" ")
            for argument in inst.args:
                print(argument.value, end=" ")
            print("")

        if name == "MOVE":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML
            else:
                assign_to_var(inst.args[0], symb_check(inst.args[1]))

        elif name == "CREATEFRAME":
            TF = {}

        elif name == "PUSHFRAME":
            try:
                LF.append(TF)
            except NameError:
                exit(55)

            LFTop = LFTop + 1
            del TF

        elif name == "POPFRAME":
            if LFTop == -1:
                exit(55)

            try:
                TF = LF[LFTop]
            except NameError or IndexError:
                exit(55)

            LFTop = LFTop - 1

        elif name == "DEFVAR":
            if argCount != 1 or inst.args[0].type != "var":
                exit(32)  # insufficient amount of arguments or invalid type in XML

            # arg -> var
            name = inst.args[0].value[3:]
            frame = inst.args[0].value[0:3]
            variable = var(name, "none", "undefined")

            # append matching frame
            if frame == "GF@":
                if name not in GF.keys():
                    GF[name] = variable
                else:
                    exit(52)
            elif frame == "LF@":
                if LFTop == -1:
                    exit(55)
                if name not in LF[LFTop].keys():
                    LF[LFTop][name] = variable
                else:
                    exit(52)
            elif frame == "TF@":
                try:
                    if name not in TF.keys():
                        TF[name] = variable
                    else:
                        exit(52)
                except NameError:
                    exit(55)
            else:
                exit(1)  # invalid frame

        elif name == "CALL":
            if argCount != 1:
                exit(32)  # insufficient amount of arguments in XML

            if inst.args[0].type != "label":
                exit(53)  # invalid type

            callStackTop = callStackTop + 1
            callStack.append(i)
            if inst.args[0].value not in labels.keys():
                exit(52)
            else:
                i = labels[inst.args[0].value]

        elif name == "RETURN":
            if argCount != 0:
                exit(32)  # return requires 0 arguments

            if callStackTop == -1:
                exit(56)
            else:
                i = callStack[callStackTop]
                callStack.remove(callStack[callStackTop])
                callStackTop = callStackTop - 1

        elif name == "PUSHS":
            if argCount != 1:
                exit(32)  # insufficient amount of arguments in XML

            dataStackTop = dataStackTop + 1
            dataStack.append(symb_check(inst.args[0]))

        elif name == "POPS":
            if argCount != 1:
                exit(32)  # insufficient amount of arguments in XML

            if dataStackTop == -1:
                exit(56)
            else:
                assign_to_var(inst.args[0], dataStack[dataStackTop])
                dataStack.remove(dataStack[dataStackTop])
                dataStackTop = dataStackTop - 1

        elif name == "ADD":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "int" or symb2.type != "int":
                exit(53)  # invalid types

            # calculate and assign
            symb1.value = int(symb1.value) + int(symb2.value)
            assign_to_var(inst.args[0], symb1)

        elif name == "SUB":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "int" or symb2.type != "int":
                exit(53)  # invalid types

            # calculate and assign
            symb1.value = int(symb1.value) - int(symb2.value)
            assign_to_var(inst.args[0], symb1)

        elif name == "MUL":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "int" or symb2.type != "int":
                exit(53)  # invalid types

            # calculate and assign
            symb1.value = int(symb1.value) * int(symb2.value)
            assign_to_var(inst.args[0], symb1)

        elif name == "IDIV":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "int" or symb2.type != "int":
                exit(53)  # invalid types

            if symb2.value == 0:
                exit(57)  # zero division

            # calculate and assign
            symb1.value = int(int(symb1.value) / int(symb2.value))
            assign_to_var(inst.args[0], symb1)

        elif name == "LT":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb2.type != symb1.type:
                exit(53)  # invalid types

            # comparison for different types
            if symb1.type == "int":
                if int(symb1.value) < int(symb2.value):
                    symb1.value = "true"
                else:
                    symb1.value = "false"
            elif symb1.type == "bool":
                if symb1.value == "false" and symb2.value == "true":
                    symb1.value = "true"
                else:
                    symb1.value = "false"
            elif symb1.type == "string":
                if symb1.value < symb2.value:
                    symb1.value = "true"
                else:
                    symb1.value = "false"
            else:
                exit(53)  # invalid types

            # assign result of type bool
            symb1.type = "bool"
            assign_to_var(inst.args[0], symb1)

        elif name == "GT":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb2.type != symb1.type:
                exit(53)  # invalid types

            # comparison for different types
            if symb1.type == "int":
                if int(symb1.value) > int(symb2.value):
                    symb1.value = "true"
                else:
                    symb1.value = "false"
            elif symb1.type == "bool":
                if not (symb1.value == "true" and symb2.value == "false"):
                    symb1.value = "false"
            elif symb1.type == "string":
                if symb1.value > symb2.value:
                    symb1.value = "true"
                else:
                    symb1.value = "false"
            else:
                exit(53)  # invalid types

            # assign result of type bool
            symb1.type = "bool"
            assign_to_var(inst.args[0], symb1)

        elif name == "EQ":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            # nil exception
            if symb1.type == "nil" or symb2.type == "nil":
                if (symb1.type == "nil" and symb2.value == "") or \
                        (symb2.type == "nil" and symb1.value == "") or \
                        (symb1.type == 'nil' and symb2.type == "nil"):
                    symb1.value = "true"
                else:
                    symb1.value = "false"

            # other types
            else:
                if symb2.type != symb1.type:
                    exit(53)  # invalid types

                # comparison for different types
                if symb1.type == "int":
                    if symb1.value == symb2.value:
                        symb1.value = "true"
                    else:
                        symb1.value = "false"
                elif symb1.type in ["bool", "string"]:
                    if symb1.value == symb2.value:
                        symb1.value = "true"
                    else:
                        symb1.value = "false"
                else:
                    exit(53)  # invalid types

            # assign result of type bool
            symb1.type = "bool"
            assign_to_var(inst.args[0], symb1)

        elif name == "AND":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "bool" or symb2.type != symb1.type:
                exit(53)  # invalid types

            # unless both symb values are true assign false else true
            if not (symb1.value == symb2.value and symb1.value == "true"):
                symb1.value = "false"
            assign_to_var(inst.args[0], symb1)

        elif name == "OR":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symbs semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            if symb1.type != "bool" or symb2.type != symb1.type:
                exit(53)  # invalid types

            # if at least one symb value is true assign true else false
            if symb1.value == "true" or symb2.value == "true":
                symb1.value = "true"
            else:
                symb1.value = "false"
            assign_to_var(inst.args[0], symb1)

        elif name == "NOT":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML

            # symb semantic validation
            symb = symb_check(inst.args[1])
            if symb.type != "bool":
                exit(53)  # invalid types

            # negate symb value
            if symb.value == "true":
                symb.value = "false"
            else:
                symb.value = "true"

            # assign result of type bool
            assign_to_var(inst.args[0], symb)

        elif name == "INT2CHAR":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML

            # symb semantic validation
            symb = symb_check(inst.args[1])

            if symb.type != "int":
                exit(53)  # invalid types

            # convert int to Unicode character
            try:
                symb.value = chr(int(symb.value))
            except ValueError or NameError or TypeError:
                exit(58)

            # assign result of type string
            symb.type = "string"
            assign_to_var(inst.args[0], symb)

        elif name == "STRI2INT":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            # symb semantic validation
            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            if symb1.type != "string" or symb2.type != "int":
                exit(53)  # invalid types

            if symb2.value < 0:
                exit(58)

            # convert string to ordinal value of Unicode character
            try:
                symb1.value = ord(symb1.value[symb2.value])
            except IndexError:
                exit(58)

            # assign result of type int
            symb1.type = "int"
            assign_to_var(inst.args[0], symb1)

        elif name == "READ":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML

            if inst.args[1].type != "type" or inst.args[1].value not in ["string", "bool", "int"]:
                exit(32)
            try:
                prompt = arg(inst.args[1].value, nextLine)
            except NameError:
                prompt = arg(inst.args[1].value, f.readline())
            prompt.value = prompt.value.replace("\n", "")
            x = x + 1
            nextLine = f.readline()
            if (prompt.type == "int" and not is_int(prompt.value)) or (nextLine == '' and prompt.value == ''):
                prompt.type = "nil"
                prompt.value = "nil"
            elif prompt.value == '':
                prompt.type = "string"
                prompt.value = ""
            elif prompt.type == "bool":
                if prompt.value.lower() == "true":
                    prompt.value = "true"
                else:
                    prompt.value = "false"
            elif prompt.value == '':
                prompt.type = "string"
                prompt.value = ""

            assign_to_var(inst.args[0], prompt)

        elif name == "WRITE":
            if argCount != 1:
                exit(32)  # invalid number of arguments

            # write to stdout
            res = symb_check(inst.args[0])
            if res.type == "nil" and (str(res.value) == "nil" or res.value == "" or res.value == "false"):
                output = str(output) + ""
            else:
                output = str(output) + str(res.value)

        elif name == "CONCAT":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            if symb1.type != symb2.type or symb1.type != "string":
                exit(53)  # invalid types

            symb1.value = symb1.value + symb2.value
            assign_to_var(inst.args[0], symb1)

        elif name == "STRLEN":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML

            symb = symb_check(inst.args[1])

            if symb.type != "string":
                exit(53)

            symb.type = "int"
            symb.value = len(symb.value)
            assign_to_var(inst.args[0], symb)

        elif name == "GETCHAR":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            if symb1.type != "string" or symb2.type != "int":
                exit(53)  # invalid types

            if symb2.value >= len(symb1.value) or symb2.value < 0:
                exit(58)
            else:
                symb1.value = symb1.value[symb2.value]

            assign_to_var(inst.args[0], symb1)

        elif name == "SETCHAR":
            if argCount != 3:
                exit(32)  # insufficient amount of arguments in XML

            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])
            tempString = symb_check(inst.args[0])

            if symb1.type != "int" or symb2.type != "string" or tempString.type != "string":
                exit(53)  # invalid types

            if symb1.value < 0:
                exit(58)

            symb1.type = "string"
            try:
                tempString.value = tempString.value.replace(tempString.value[int(symb1.value)], symb2.value[0])
            except IndexError:
                exit(58)
            symb1.value = tempString.value
            assign_to_var(inst.args[0], symb1)

        elif name == "TYPE":
            if argCount != 2:
                exit(32)  # insufficient amount of arguments in XML

            symb = inst.args[1]

            if symb.type == "var":
                frame = symb.value[0:3]
                name = symb.value[3:]
                if frame == "GF@" and name in GF.keys():
                    if GF[name].value == "none":
                        symb.value = ""
                        symb.type = "nil"
                    else:
                        symb.value = GF[name].type
                        symb.type = "string"
                elif frame == "LF@":
                    if LFTop == -1:
                        exit(55)
                    if name in LF[LFTop].keys():
                        if LF[LFTop][name].value == "none":
                            symb.value = ""
                            symb.type = "nil"
                        else:
                            symb.value = LF[LFTop][name].type
                            symb.type = "string"
                    else:
                        exit(54)
                elif frame == "TF@":
                    try:
                        if name in TF.keys():
                            if TF[name].value == "none":
                                symb.value = "nil"
                                symb.type = "nil"
                            else:
                                symb.value = TF[name].type
                                symb.type = "string"
                        else:
                            exit(54)
                    except NameError:
                        exit(55)
                else:
                    exit(54)  # undefined variable
            else:
                symb.value = symb.type
                symb.type = "string"

            assign_to_var(inst.args[0], symb)

        elif name == "JUMP":
            if argCount != 1:
                exit(32)

            if inst.args[0].type != "label":
                exit(53)

            if inst.args[0].value not in labels.keys():
                exit(52)
            else:
                i = labels[inst.args[0].value]

        elif name == "JUMPIFEQ":
            if argCount != 3:
                exit(32)

            if inst.args[0].type != "label":
                exit(53)

            if inst.args[0].value not in labels.keys():
                exit(52)

            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            # nil exception
            if symb1.type == "nil" or symb2.type == "nil":
                if (symb1.type == "nil" and symb2.value == "") or \
                        (symb2.type == "nil" and symb1.value == "") or \
                        (symb1.type == 'nil' and symb2.type == "nil"):
                    result = True
                else:
                    result = False

            # other types
            else:
                if symb2.type != symb1.type:
                    exit(53)  # invalid types

                # comparison for different types
                if symb1.type == "int":
                    if symb1.value == symb2.value:
                        result = True
                    else:
                        result = False
                elif symb1.type in ["bool", "string"]:
                    if symb1.value == symb2.value:
                        result = True
                    else:
                        result = False
                else:
                    exit(53)  # invalid types

            if result:
                i = labels[inst.args[0].value]

        elif name == "JUMPIFNEQ":
            if argCount != 3:
                exit(32)

            if inst.args[0].type != "label":
                exit(53)

            if inst.args[0].value not in labels.keys():
                exit(52)

            symb1 = symb_check(inst.args[1])
            symb2 = symb_check(inst.args[2])

            # nil exception
            if symb1.type == "nil" or symb2.type == "nil":
                if (symb1.type == "nil" and symb2.value == "") or \
                        (symb2.type == "nil" and symb1.value == "") or \
                        (symb1.type == 'nil' and symb2.type == "nil"):
                    result = True
                else:
                    result = False

            # other types
            else:
                if symb2.type != symb1.type:
                    exit(53)  # invalid types

                # comparison for different types
                if symb1.type == "int":
                    if symb1.value == symb2.value:
                        result = True
                    else:
                        result = False
                elif symb1.type in ["bool", "string"]:
                    if symb1.value == symb2.value:
                        result = True
                    else:
                        result = False
                else:
                    exit(53)  # invalid types

            if not result:
                i = labels[inst.args[0].value]

        elif name == "EXIT":
            if argCount != 1:
                exit(32)

            symb = symb_check(inst.args[0])

            if symb.type != "int":
                exit(53)

            if not (symb.value > -1 and symb.value < 50):
                exit(57)
            else:
                if output != "":
                    output = replace_dec(output)
                    print(output, end="")
                exit(symb.value)

        elif name == "DPRINT":
            if argCount != 1:
                exit(32)

            symb = symb_check(inst.args[0])

            # if symb.type != "int":
            #     exit(53)

            #print(symb.value, file=sys.stderr)

        elif name == "BREAK":
            #print("Code position: " + inst.opcode + "\n" + "Instructions performed:" + instCount, file=sys.stderr)
            i = i + 1
            continue

        elif name == "LABEL":
            i = i + 1
            continue

        else:
            exit(32)  # invalid instruction opcode in XML

        instCount = instCount + 1
        i = i + 1

    if output != "":
        output = replace_dec(output)
        print(output, end="")
