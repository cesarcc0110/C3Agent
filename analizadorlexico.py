# Analizador léxico basado en DFA con identificación por Token ID
# Este analizador léxico utiliza una máquina de estados finitos determinista (DFA)
# para reconocer tokens definidos

# Diccionario de Token IDs definido por el usuario
# Cada clave es un lexema reconocido y su valor es el ID único asignado.
TOKEN_IDS = {
    "class": 1, "virtual": 2, "override": 3, "this": 4, "extends": 5,
    "abstract": 6, "public": 7, "private": 8, "protected": 9, "switch": 10,
    "case": 11, "break": 12, "continue": 13, "do": 14, "*": 15, "{": 16,
    "}": 17, "(": 18, ")": 19, "::": 20, ".": 21, ";": 22, "->": 23, ":": 24
}

# Tabla de transición del DFA
# Define cómo cambia el estado del analizador según la clase del carácter leído.
# Los estados:
# - q0: estado inicial
# - q1: estado para reconocer identificadores y palabras clave
# - q3: estado para reconocer operadores y símbolos especiales
# - qe: estado de error (no aceptado)
# - 'skip' indica que el carácter es un delimitador y debe ser ignorado.
transition_table = {
    'q0': {
        'letter_or_underscore': 'q1',      # Inicia reconocimiento de identificadores/palabras clave
        'special_op': 'q3',                # Inicia reconocimiento de operadores/símbolos
        'delimiter': 'skip',               # Ignorar caracteres delimitadores (espacios, símbolos de separación)
        'other': 'qe'                     # Cualquier otro carácter es error
    },
    'q1': {
        'letter_or_underscore_or_digit': 'q1',  # Continúa identificador o palabra clave
        'delimiter': 'q2'                        # Estado de aceptación al encontrar delimitador
    },
    'q3': {
        'delimiter': 'q2'                        # Estado de aceptación para operadores/símbolos tras un carácter especial
    }
}

# Conjunto de estados aceptadores del DFA
accepting_states = {'q2'}

def classify(ch):
    """
    Clasifica un carácter en una categoría utilizada para la transición del DFA.
    - letter_or_underscore: letras o guion bajo, para iniciar identificadores.
    - letter_or_underscore_or_digit: letras, guion bajo o dígitos, para continuar identificadores.
    - delimiter: espacios, tabulaciones y símbolos que separan tokens.
    - special_op: caracteres que pueden ser operadores o símbolos especiales.
    - other: cualquier otro carácter no reconocido.
    """
    if ch.isalpha() or ch == '_':
        return 'letter_or_underscore'
    elif ch.isdigit():
        return 'letter_or_underscore_or_digit'
    elif ch.isspace() or ch in ";:(){}[]":
        return 'delimiter'
    elif ch in "".join(TOKEN_IDS.keys()):
        return 'special_op'
    else:
        return 'other'

def is_accepting(state):
    """
    Verifica si un estado es un estado aceptador del DFA.
    """
    return state in accepting_states

def scanner_user_tokens_with_ids(input_string):
    """
    Función principal del analizador léxico.
    Toma una cadena de entrada y devuelve una lista de tokens reconocidos,
    cada uno representado como una tupla (Token ID, lexema).
    
    El analizador recorre la cadena caracter por caracter, utilizando el DFA para
    identificar tokens válidos según la tabla de transiciones y las reglas definidas.
    Los tokens reconocidos deben estar en el diccionario TOKEN_IDS para ser emitidos.
    """
    i = 0
    tokens = []
    while i < len(input_string):
        state = 'q0'     # Estado inicial para cada nuevo token
        lexeme = ''      # Acumulador del lexema actual
        while i < len(input_string):
            ch = input_string[i]
            char_class = classify(ch)  # Clasifica el carácter actual
            
            if state == 'q0':
                # Estado inicial: decidir qué tipo de token comenzar a reconocer
                if char_class == 'letter_or_underscore':
                    state = transition_table['q0']['letter_or_underscore']
                    lexeme += ch
                    i += 1
                elif char_class == 'special_op':
                    state = transition_table['q0']['special_op']
                    lexeme += ch
                    i += 1
                elif char_class == 'delimiter':
                    # Delimitadores se ignoran y no generan tokens
                    i += 1
                    break
                else:
                    # Carácter no reconocido, pasa a estado de error y captura el lexema
                    state = transition_table['q0']['other']
                    lexeme += ch
                    i += 1
                    break
            elif state == 'q1':
                # Reconociendo un identificador o palabra clave
                if char_class in ['letter_or_underscore', 'letter_or_underscore_or_digit']:
                    state = transition_table['q1']['letter_or_underscore_or_digit']
                    lexeme += ch
                    i += 1
                elif char_class == 'delimiter':
                    # Fin del token al encontrar un delimitador
                    state = transition_table['q1']['delimiter']
                    break
                else:
                    # Carácter inválido para identificador, error
                    state = 'qe'
                    break
            elif state == 'q3':
                # Reconociendo operador o símbolo especial
                if char_class == 'delimiter':
                    # Fin del token al encontrar delimitador
                    state = transition_table['q3']['delimiter']
                    break
                else:
                    # Carácter inválido para operador, error
                    state = 'qe'
                    break
        # Si el estado final es aceptador, y el lexema está en TOKEN_IDS, se agrega a la lista de tokens
        if is_accepting(state):
            if lexeme in TOKEN_IDS:
                tokens.append((TOKEN_IDS[lexeme], lexeme))
        # Se omiten espacios en blanco adicionales antes de continuar con el siguiente token
        while i < len(input_string) and input_string[i].isspace():
            i += 1
    return tokens

# Ejemplo de uso del analizador léxico
if __name__ == "__main__":
    test_code = """
    class Engine {
public:
    virtual void start() {
        this.extends = abstract;
    }

private:
    int power;

protected:
    void reset() {
        switch (power) {
            case 0:
                break;
            case 1:
                continue;
        }
    }
};
    """
    # Se ejecuta el analizador sobre el código de prueba y se imprimen los tokens reconocidos
    result = scanner_user_tokens_with_ids(test_code)
    for token in result:
        print(token)
