"""
  Analizador Léxico Table-Driven simplificado
  Codificado por Cesar Cabrera, Jorge Madrigal y Heber Moran
  Actualizado: Mayo 2025
"""

# Diccionario de palabras clave con su número de token
TOKENS = {
    "class": 1,
    "identifier": 2
}

# Diccionario de símbolos especiales con su número de token
SPECIAL_SYMBOLS = {
    "{": 3, "}": 4, "(": 5, ")": 6
}

# ====================== TABLA DE TRANSICIONES DEL DFA ======================

# Tipos de caracteres:
# 0 = letra, 1 = dígito, 2 = '_', 3 = delimitador, 4 = otro
T = [
    [1, None, 1, None, None],    # q0
    [1, 1, 1, 2, None],          # q1
    [None, None, None, None, None]  # q2 (estado de aceptación)
]

# Estados de aceptación
ACCEPTING = [0, 0, 1]

# ====================== FUNCIONES AUXILIARES DEL DFA ======================
def classify(ch):
    if ch.isalpha():
        return 0  # letra
    elif ch.isdigit():
        return 1  # dígito
    elif ch == '_':
        return 2  # guion bajo
    elif ch in [' ', '\n', '\t']:
        return 3  # delimitador
    else:
        return 4  # otro (no permitido)

def is_accepting(state):
    return ACCEPTING[state] == 1

def next_input_char(input_string, i):
    return input_string[i] if i < len(input_string) else None

# ====================== ANALIZADOR LÉXICO PRINCIPAL ======================
def lexical_scanner(input_string):
    tokens = []
    symbol_table = []
    i = 0

    while i < len(input_string):
        ch = next_input_char(input_string, i)

        if ch in SPECIAL_SYMBOLS:
            tokens.append((SPECIAL_SYMBOLS[ch],))
            i += 1
            continue

        elif ch in [' ', '\n', '\t']:
            i += 1
            continue

        state = 0
        lexeme = ""

        while True:
            ch = next_input_char(input_string, i)
            if ch is None:
                break

            ch_type = classify(ch)
            next_state = T[state][ch_type]

            if next_state is not None and ch_type in [0, 1, 2]:
                lexeme += ch
                i += 1
                state = next_state
            elif (ch_type == 3 or ch in SPECIAL_SYMBOLS) and T[state][3] is not None:
                # símbolo o delimitador fuerza aceptación
                state = T[state][3]
                break
            else:
                break

        if is_accepting(state) and lexeme != "":
            if lexeme == "class":
                tokens.append((TOKENS["class"],))
            else:
                if lexeme not in symbol_table:
                    symbol_table.append(lexeme)
                idx = symbol_table.index(lexeme) + 1
                tokens.append((TOKENS["identifier"], idx))  # 2 = identificador
        else:
            i += 1

    return tokens, symbol_table

# ====================== BLOQUE PRINCIPAL ======================
if __name__ == "__main__":
    try:
        with open("entrada.txt", "r", encoding="utf-8") as archivo:
            source_code = archivo.read()
    except FileNotFoundError:
        print("No se encontró el archivo 'entrada.txt'. Asegúrate de que esté en el mismo directorio.")
        exit()

    # Ejecutar el analizador
    tokens, symbols = lexical_scanner(source_code)

    # Escribir la salida en un archivo
    with open("tokens.txt", "w", encoding="utf-8") as out_file:
        out_file.write("Tokens Reconocidos:\n")
        for token in tokens:
            if len(token) == 2:
                out_file.write(f"<{token[0]},{token[1]}>\n")
            else:
                out_file.write(f"<{token[0]}>\n")

        out_file.write("\nTabla de Símbolos (Identifiers):\n")
        for idx, sym in enumerate(symbols):
            out_file.write(f"{idx + 1}: {sym}\n")

    print("Análisis léxico completado. Revisa el archivo 'tokens.txt'.")