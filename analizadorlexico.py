"""
  Analizador Léxico Table-Driven para lenguajes de programación
  Codificado por Cesar Cabrera, Jorge Madrigal y Heber Moran
  Mayo 2025.
"""

# Diccionario de palabras clave con su número de token
TOKENS = {
    "class": 1, "virtual": 2, "override": 3, "this": 4, "extends": 5, "abstract": 6,
    "public": 7, "private": 8, "protected": 9, "switch": 10, "case": 11, "break": 12,
    "continue": 13, "do": 14
}

# Diccionario de símbolos especiales con su número de token
SPECIAL_SYMBOLS = {
    "*": 15, "{": 16, "}": 17, "(": 18, ")": 19, "::": 20,
    ".": 21, ";": 22, "->": 23, ":": 24
}

# ====================== TABLA DE TRANSICIONES DEL DFA ======================

# Tabla T: T[estado][tipo_de_caracter]
# Tipos de caracteres:
# 0 = letra, 1 = dígito, 2 = '_', 3 = delimitador, 4 = símbolo especial, 5 = otro
T = [
    [1, 3, 1, 3, 3, 3],  # estado 0: inicio
    [1, 1, 1, 2, 3, 3],  # estado 1: acumulando identificador
    [1, 1, 1, 2, 3, 3],  # estado 2: aceptación (pero puede seguir acumulando)
    [3, 3, 3, 3, 3, 3],  # estado 3: error
]

# Estados de aceptación (1 = sí, 0 = no)
ACCEPTING = [0, 0, 1, 0]
ERROR = 3

# ====================== FUNCIONES AUXILIARES DEL DFA ======================
def classify(ch):
    """ 
      Clasifica el carácter ch según el tipo necesario para la tabla de transición del DFA.
      Retorna un número entero entre 0 y 5.
    """
    if ch.isalpha():
        return 0  # letra
    elif ch.isdigit():
        return 1  # dígito
    elif ch == '_':
        return 2  # guion bajo
    elif ch in [' ', '\n', '\t', ';', '(', ')', '{', '}', ':', '.', ',']:
        return 3  # delimitador
    elif ch in SPECIAL_SYMBOLS:
        return 4  # símbolo especial
    else:
        return 5  # otro (error)

# Retorna si un estado es de aceptación
def is_accepting(state):
    return ACCEPTING[state] == 1

# Retorna si un estado es de error
def is_error(state):
    return state == ERROR

# Determina si se debe avanzar al siguiente carácter
def advance(state, ch_type):
    return not (is_accepting(state) and ch_type == 3)

# Lee el siguiente carácter de la entrada
def next_input_char(input_string, i):
    return input_string[i] if i < len(input_string) else None

# ====================== ANALIZADOR LÉXICO PRINCIPAL ======================

def lexical_scanner(input_string):
    tokens = []        # lista de tokens reconocidos
    symbol_table = []  # tabla de identificadores
    i = 0              # posición del puntero en el input

    while i < len(input_string):
        ch = next_input_char(input_string, i)

        # --- Procesar símbolos compuestos :: y ->
        if input_string[i:i+2] == "::":
            tokens.append((SPECIAL_SYMBOLS["::"],))
            i += 2
            continue
        elif input_string[i:i+2] == "->":
            tokens.append((SPECIAL_SYMBOLS["->"],))
            i += 2
            continue

        # --- Procesar símbolos especiales simples
        elif ch in SPECIAL_SYMBOLS:
            tokens.append((SPECIAL_SYMBOLS[ch],))
            i += 1
            continue

        # --- Ignorar espacios en blanco
        elif ch in [' ', '\n', '\t']:
            i += 1
            continue

        # --- Verificar si puede iniciar un identificador
        if classify(ch) not in [0, 2]:  # si no es letra ni '_'
            start = i
            lexeme = ""
            while i < len(input_string):
                ch = input_string[i]
                if classify(ch) == 3:  # si es delimitador, se detiene
                    break
                lexeme += ch
                i += 1
            print(f"[Error léxico] Token inválido: '{lexeme}'")
            continue

        # ---------- INICIO DEL DFA ----------
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

            if ch_type != 3:
                lexeme += ch  # acumulamos el lexema

            if advance(state, ch_type):
                i += 1
            else:
                break
        # ---------- FIN DEL DFA ----------

        # --- Guardar token reconocido o mostrar error
        if is_accepting(state) and lexeme != "":
            if lexeme in TOKENS:
                tokens.append((TOKENS[lexeme],))  # palabra clave
            else:
                if lexeme not in symbol_table:
                    symbol_table.append(lexeme)
                idx = symbol_table.index(lexeme) + 1
                tokens.append((25, idx))  # identificador
        elif lexeme != "":
            print(f"[Error léxico] Token inválido: '{lexeme}'")
        else:
            i += 1

    return tokens, symbol_table

# ====================== BLOQUE PRINCIPAL (lectura desde archivo) ======================

if __name__ == "__main__":
    try:
        with open("entrada.txt", "r", encoding="utf-8") as archivo:
            source_code = archivo.read()
    except FileNotFoundError:
        print("No se encontró el archivo 'entrada.txt'. Asegúrate de que esté en el mismo directorio.")
        exit()

    # Ejecutar el analizador
    tokens, symbols = lexical_scanner(source_code)

    # Mostrar tokens reconocidos
    print("\nTokens Reconocidos:")
    for token in tokens:
        if len(token) == 2:
            print(f"<{token[0]},{token[1]}>  {symbols[token[1]-1]}")
        else:
            lex = next((k for k, v in TOKENS.items() if v == token[0]), None)
            if lex is None:
                lex = next((k for k, v in SPECIAL_SYMBOLS.items() if v == token[0]), None)
            print(f"<{token[0]}> {lex if lex else ''}")

    # Mostrar tabla de símbolos (identificadores)
    print("\nTabla de Símbolos (Identifiers):")
    for idx, sym in enumerate(symbols):
        print(f"{idx + 1}: {sym}")
