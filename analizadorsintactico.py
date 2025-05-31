"""
  Analizador Sintáctico
  Codificado por Cesar Cabrera, Jorge Madrigal y Heber Moran
  Actualizado: Mayo 2025
"""

# Tabla que define qué producción aplicar según el no terminal y el token actual
parsing_table = {
    "<TYPE>": {
        2: 1,  
        1: 2,  
        5: 3, 
        3: 4,  
        6: 5,  
        4: 5,  
        "$": 5 
    },
    "<CLOSER>": {
        2: 8, 1: 8, 5: 8, 3: 8, "$": 8,  # → ε
        6: 6, 
        4: 7   
    }
}

# Producciones asociadas a sus números
productions = {
    1: [2, "<TYPE>"],                      
    2: [1, "<TYPE>"],                        
    3: [5, "<TYPE>", "<CLOSER>", "<TYPE>"],  
    4: [3, "<TYPE>", "<CLOSER>", "<TYPE>"],  
    5: [],                                
    6: [6, "<CLOSER>"],                     
    7: [4, "<CLOSER>"],                      
    8: []                                   
}

# Función para cargar los tokens desde un archivo
def load_tokens(path):
    tokens = []
    with open(path, 'r') as file:
        for line in file:
            line = line.strip()
            if line == "$":
                tokens.append("$")  
            elif line.startswith("<"):
                content = line[1:-1]
                token_type = int(content.split(",")[0]) if "," in content else int(content)
                tokens.append(token_type)
    tokens.append("$")  
    return tokens

# Función principal del parser predictivo LL(1)
def parse(tokens):
    stack = ["$", "<TYPE>"]  
    index = 0
    token = tokens[index]

    # Flags para clasificación final
    seen_class = False     
    seen_block = False     
    seen_paren = False     
    seen_id = False        

    applied_productions = []  # para rastrear qué producciones se usaron

    # Proceso de análisis sintáctico
    while stack[-1] != "$":
        top = stack.pop()

        if top == token:
            index += 1
            token = tokens[index] if index < len(tokens) else "$"

        elif isinstance(top, int) or top == "$":
            print(f"Error: se esperaba token {top} pero se encontró {token}")
            print("✖ Código INVÁLIDO")
            return

        elif top in parsing_table:
            if token in parsing_table[top]:
                prod_number = parsing_table[top][token]
                rhs = productions[prod_number]
                applied_productions.append(prod_number)

                if prod_number == 1:
                    seen_id = True
                elif prod_number == 2:
                    seen_class = True
                elif prod_number == 3:
                    seen_paren = True
                elif prod_number == 4:
                    seen_block = True

                for symbol in reversed(rhs):
                    stack.append(symbol)
            else:
                print(f"Error: no hay regla para [{top}, {token}] en la tabla de parsing")
                print("✖ Código INVÁLIDO")
                return
        else:
            print(f"Error: símbolo desconocido en el stack: {top}")
            print("✖ Código INVÁLIDO")
            return

    if token == "$":
        print("✔ Análisis sintáctico correcto.")

        is_oop = seen_class and seen_block
        is_pp = seen_paren and seen_block

        if is_oop and is_pp:
            print("→ Clasificación: CÓDIGO HÍBRIDO (OOP + PP)")
        elif is_oop:
            print("→ Clasificación: CÓDIGO ORIENTADO A OBJETOS (OOP)")
        elif is_pp:
            print("→ Clasificación: CÓDIGO PROCEDIMENTAL (PP)")
        elif seen_id:
            print("→ Clasificación: TEXTO / DECLARACIONES SUELTAS")
        else:
            print("→ Clasificación: CÓDIGO NO CLASIFICABLE")
    else:
        print("Error: tokens restantes tras vaciar la pila.")
        print("✖ Código INVÁLIDO")


if __name__ == "__main__":
    tokens = load_tokens("tokens.txt")
    parse(tokens)