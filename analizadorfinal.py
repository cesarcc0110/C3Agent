# Definición de palabras clave y símbolos especiales
TOKENS = {
    "class": 1, "virtual": 2, "override": 3, "this": 4, "extends": 5, "abstract": 6,
    "public": 7, "private": 8, "protected": 9, "switch": 10, "case": 11, "break": 12,
    "continue": 13, "do": 14, "void": 15
}

SPECIAL_SYMBOLS = {
    "*": 15, "{": 16, "}": 17, "(": 18, ")": 19, "::": 20,
    ".": 21, ";": 22, "->": 23, ":": 24
}

# Tabla DFA: columnas → 0=letra, 1=dígito, 2=_, 3=delimitador, 4=símbolo especial, 5=otro
T = [
    [1, 3, 1, 3, 3, 3],  # estado 0
    [1, 1, 1, 2, 3, 3],  # estado 1
    [1, 1, 1, 2, 3, 3],  # estado 2 (aceptación)
    [3, 3, 3, 3, 3, 3],  # estado 3 (error)
]

ACCEPTING = [0, 0, 1, 0]
ERROR = 3

def classify(ch):
    if ch.isalpha():
        return 0
    elif ch.isdigit():
        return 1
    elif ch == '_':
        return 2
    elif ch in [' ', '\n', '\t', ';', '(', ')', '{', '}', ':', '.', ',']:
        return 3
    elif ch in SPECIAL_SYMBOLS:
        return 4
    else:
        return 5

def is_accepting(state):
    return ACCEPTING[state] == 1

def is_error(state):
    return state == ERROR

def advance(state, ch_type):
    return not (is_accepting(state) and ch_type == 3)

def next_input_char(input_string, i):
    return input_string[i] if i < len(input_string) else None

def lexical_scanner(input_string):
    tokens = []
    symbol_table = []
    i = 0

    while i < len(input_string):
        ch = next_input_char(input_string, i)

        # Casos especiales de dos caracteres
        if input_string[i:i+2] == "::":
            tokens.append((SPECIAL_SYMBOLS["::"],))
            i += 2
            continue
        elif input_string[i:i+2] == "->":
            tokens.append((SPECIAL_SYMBOLS["->"],))
            i += 2
            continue
        elif ch in SPECIAL_SYMBOLS:
            tokens.append((SPECIAL_SYMBOLS[ch],))
            i += 1
            continue
        elif ch in [' ', '\n', '\t']:
            i += 1
            continue

        # ---------- INICIO DEL DFA COMO EN LAS IMÁGENES ----------
        state = 0
        lexeme = ""

        while not is_accepting(state) and not is_error(state):
            ch = next_input_char(input_string, i)
            if ch is None:
                break
            ch_type = classify(ch)
            state = T[state][ch_type]

            if is_error(state):
                break

            if ch_type != 3:  # evitar espacios en el lexema
                lexeme += ch

            if advance(state, ch_type):
                i += 1
            else:
                break
        # ---------- FIN DEL DFA ----------

        if is_accepting(state) and lexeme != "":
            if lexeme in TOKENS:
                tokens.append((TOKENS[lexeme],))
            else:
                if lexeme not in symbol_table:
                    symbol_table.append(lexeme)
                idx = symbol_table.index(lexeme) + 1
                tokens.append((25, idx))
        elif lexeme != "":
            print(f"[Error léxico] Token inválido: '{lexeme}'")
            i += 1
        else:
            i += 1

    return tokens, symbol_table

# Leer archivo
with open("entrada.txt", "r") as archivo:
    source_code = archivo.read()

# Ejecutar analizador
tokens, symbols = lexical_scanner(source_code)

# Imprimir resultados
print("Tokens Reconocidos:")
for token in tokens:
    if len(token) == 2:
        print(f"<{token[0]},{token[1]}>  {symbols[token[1]-1]}")
    else:
        # Obtener nombre del token
        lex = next((k for k, v in TOKENS.items() if v == token[0]), None)
        if lex is None:
            lex = next((k for k, v in SPECIAL_SYMBOLS.items() if v == token[0]), None)
        print(f"<{token[0]}> {lex if lex else ''}")

print("\nTabla de Símbolos (Identifiers):")
for idx, sym in enumerate(symbols):
    print(f"{idx + 1}: {sym}")