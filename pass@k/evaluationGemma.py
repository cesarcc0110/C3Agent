import os
import subprocess
import csv
import json
import re
from pathlib import Path

REPO_URL = "https://github.com/HeberM69/Test_C3"
CONFIG_PATH = "/Users/estebanm/Documents/C3Agent/SWE-agent/config/coding_challenge.yaml"
PROBLEMS_FILE = "problems.txt"
OUTPUT_BASE = "./runs"
RUNS_PER_TASK = 3
CSV_OUTPUT = "resultados.csv"
JSONL_PATH = "./test.jsonl"  # Ajusta esto a tu path real
branch_name = "sweagent_evaluation"

def run_swe_agent(problem_url, run_idx, problem_id):
    run_dir = os.path.join(OUTPUT_BASE, f"{problem_id}run{run_idx}")
    os.makedirs(run_dir, exist_ok=True)

    cmd = [
        "sweagent", "run",
        "--config", CONFIG_PATH,
        f"--env.repo.github_url={REPO_URL}",
        f"--problem_statement.github_url={problem_url}"
    ]

    print(f"→ Ejecutando SWE-agent [tarea {problem_id} - intento {run_idx + 1}]...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    with open(os.path.join(run_dir, "stdout.txt"), "w") as f:
        f.write(result.stdout)
    with open(os.path.join(run_dir, "stderr.txt"), "w") as f:
        f.write(result.stderr)

    return run_dir

def load_test_case(issue_id):
    with open(JSONL_PATH, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["issue"] == issue_id:
                return data["input"], data["expected_output"]
    return None, None

def execute_code_with_input(file_path, test_input):
    try:
        result = subprocess.run(
            ["python3", file_path],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"❗ Error al ejecutar el archivo {file_path}: {e}")
        return None
    
def load_java_test(issue_id):
    with open(JSONL_PATH, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["issue"] == issue_id:
                return data["test"]
    return None

def fix_common_patch_path_errors(path: str) -> str:
    """
    Corrige errores comunes en rutas de archivos, incluyendo:
    - 'Ci12' → 'C3-i12'
    - 'chlenge' → 'challenge'
    """
    corrections = {
        r'__Test_Ci(\d+)': r'__Test_C3-i\1',
        r'coding_chlenge': 'coding_challenge',
        r'codinghallenge': 'coding_challenge',
        r'coding_chlenge': 'coding_challenge',
        r'codinghallenge': 'coding_challenge',
        r'codegmeama': 'codegemma',
        r'codegemna': 'codegemma',
        r'codegmemma': 'codegemma',
        r'cegemma': 'codegemma',
        r'ollma': 'ollama',
        r'olma': 'ollama',
        r'oama': 'ollama',  
        r'\.tch\.patch$': '.patch',  # para final malformado  codemma
        r'H(e|)berM69': 'HeberM69',  # capturar variantes menores de Heber
        r'codemma': 'codegemma',  # corregir codemma a codegemma
    }

    for pattern, replacement in corrections.items():
        path = re.sub(pattern, replacement, path)

    return path

def write_test_file(issue_id, run_dir, test_file_path="test.jsonl"):
    with open(test_file_path, "r") as f:
        for line in f:
            test_data = json.loads(line)
            if test_data["issue"] == issue_id:
                test_code = test_data["test"]
                test_path = Path(run_dir) / "SolutionTest.java"
                with open(test_path, "w") as tf:
                    tf.write(test_code)
                print(f"🧪 Test JUnit para issue {issue_id} escrito en {test_path}")
                return True
    print(f"⚠️ No se encontró test.jsonl para issue {issue_id}")
    return False

def extract_patch_path(log: str) -> str:
    match = re.search(r"PATCH_FILE_PATH='([^']+)'", log, re.DOTALL)
    if match:
        raw_path = match.group(1)
        cleaned_path = raw_path.replace('\n', '').replace(' ', '').strip()

        # Asegura que termine con .patch correctamente
        if not cleaned_path.endswith('.patch'):
            if cleaned_path.endswith('patch') and not cleaned_path.endswith('.patch'):
                cleaned_path = re.sub(r'(patch)$', r'.\1', cleaned_path)
            else:
                cleaned_path += '.patch'

        # Corregir errores comunes como 'Ci12' en lugar de 'C3-i12'
        cleaned_path = fix_common_patch_path_errors(cleaned_path)

        return cleaned_path
    else:
        print("❌ No se encontró PATCH_FILE_PATH en el log.")
        return None

def evaluate_cpp_patch(repo_path, issue_id):
    # Función para cargar test C++ asociado a issue_id (debes implementarla)
    cpp_test_code = load_java_test(issue_id)
    if not cpp_test_code:
        print(f"❌ No se encontró test C++ para issue {issue_id}")
        return False

    test_file_path = os.path.join(repo_path, "SolutionTest.cpp")
    with open(test_file_path, "w") as f:
        f.write(cpp_test_code)
    print("📝 Test C++ guardado en SolutionTest.cpp")

    # Detectar archivo .cpp modificado (excluyendo el test)
    cpp_files = [f for f in os.listdir(repo_path) if f.endswith(".cpp") and f != "SolutionTest.cpp"]
    if not cpp_files:
        print("❌ No se encontró archivo .cpp modificado para compilar.")
        return False

    source_file = cpp_files[0]  # Usamos el primero (asumimos solo uno)
    print(f"🧪 Compilando archivos: {source_file} y SolutionTest.cpp...")

    # Nombre del binario a generar
    bin_path = os.path.join(repo_path, "test_exec")

    compile_cmd = ["g++", "-std=c++17", "-o", bin_path, source_file, "SolutionTest.cpp"]

    try:
        compile_result = subprocess.run(
            compile_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if compile_result.returncode != 0:
            print("❌ Error al compilar los archivos C++:")
            print(compile_result.stderr)
            return False
    except Exception as e:
        print(f"❗ Excepción al compilar: {e}")
        return False

    # Ejecutar el binario compilado
    try:
        exec_result = subprocess.run(
            [bin_path],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        print("📋 Resultado de ejecución:")
        print(exec_result.stdout)
        print(exec_result.stderr)

        if exec_result.returncode == 0:
            print("✅ Patch pasó todos los tests C++")
            return True
        else:
            print("❌ Alguno(s) de los tests fallaron o hubo error de ejecución")
            return False

    except Exception as e:
        print(f"❗ Excepción al ejecutar binario: {e}")
        return False

def evaluate_java_patch(repo_path, issue_id):
    def build_junit_classpath():
        base_dirs = [
            os.path.expanduser("~/.m2/repository/org/junit"),
            os.path.expanduser("~/.m2/repository/org/apiguardian"),
            os.path.expanduser("~/.m2/repository/org/opentest4j"),
            os.path.expanduser("~/.m2/repository/org/jupiter"),
        ]
        jars = []
        for base in base_dirs:
            for root, _, files in os.walk(base):
                for file in files:
                    if file.endswith(".jar") and not file.endswith(("-javadoc.jar", "-sources.jar")):
                        jars.append(os.path.join(root, file))
        return ":".join(jars)

    java_test_code = load_java_test(issue_id)
    if not java_test_code:
        print(f"❌ No se encontró test JUnit para issue {issue_id}")
        return False

    test_filename = "SolutionTest.java"
    test_file_path = os.path.join(repo_path, test_filename)
    with open(test_file_path, "w") as f:
        f.write(java_test_code)
    print("📝 Test JUnit guardado en SolutionTest.java")

    classpath = build_junit_classpath()

    # Detectar archivo editado (excluyendo el test)
    java_files = [
        f for f in os.listdir(repo_path)
        if f.endswith(".java") and f != test_filename
    ]

    if not java_files:
        print("❌ No se encontró ningún archivo .java que no sea el test.")
        return False

    # Tomar el archivo editado más reciente
    java_files.sort(key=lambda f: os.path.getmtime(os.path.join(repo_path, f)), reverse=True)
    edited_java_file = java_files[0]

    compile_cmd = ["javac", "-cp", f".:{classpath}", edited_java_file, test_filename]
    print(f"🧪 Compilando archivos: {edited_java_file} y {test_filename}...")

    try:
        compile_result = subprocess.run(
            compile_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if compile_result.returncode != 0:
            print("❌ Error al compilar los archivos Java:")
            subprocess.run(
              ["git", "restore", 
              edited_java_file], 
              cwd=repo_path, check=True, 
              capture_output=True, 
              text=True, 
              timeout=10
            )
            print(compile_result.stderr)
            return False
    except Exception as e:
        print(f"❗ Excepción al compilar: {e}")
        return False

    # Ejecutar los tests con JUnit
    try:
        test_cmd = [
            "java",
            "-cp",
            f".:{classpath}",
            "org.junit.runner.JUnitCore",
            "SolutionTest"
        ]
        test_result = subprocess.run(
            test_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        print("📋 Resultado de JUnit:")
        print(test_result.stdout)

        if "FAILURES!!!" not in test_result.stdout and "Exception" not in test_result.stdout:
            print("✅ Patch pasó todos los tests JUnit")
            return True
        else:
            print("❌ Alguno(s) de los tests fallaron")
            return False

    except Exception as e:
        print(f"❗ Excepción al ejecutar JUnit: {e}")
        return False


def apply_patch_to_repo(patch_path, repo_path, run_idx):
    try:
        subprocess.run(["git", "apply", patch_path], cwd=repo_path, check=True, capture_output=True, text=True, timeout=10)
        print(f"✅ Patch aplicado correctamente en {repo_path}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al aplicar el patch en {repo_path}:")
        print(f"STDOUT: {e.stdout.strip()}")
        print(f"STDERR: {e.stderr.strip()}")
        return False
'''
def apply_patch_to_repo(patch_path, repo_path, run_idx):
    # Create a unique branch name for each run attempt
    current_branch_name = f"{branch_name}issue{os.path.basename(repo_path)[0]}_run{run_idx}"

    try:
        # 1. Ensure we're on the main branch before creating a new one
        # This is important to reset the state for each new attempt's branch
        subprocess.run(["git", "checkout", "main"], cwd=repo_path, check=True, capture_output=True, text=True, timeout=10)
        print(f"DEBUG: Switched to 'main' in {repo_path}")

        # 2. Delete the branch if it already exists (from a previous failed run of the same attempt)
        # Use check=False because the branch might not exist on the first try
        delete_result = subprocess.run(["git", "branch", "-D", current_branch_name], cwd=repo_path, capture_output=True, text=True, timeout=10)
        if delete_result.returncode == 0:
            print(f"DEBUG: Deleted existing branch {current_branch_name}")
        elif "not found" not in delete_result.stderr: # Only print error if it's not "branch not found"
             print(f"WARNING: Could not delete branch {current_branch_name}: {delete_result.stderr}")


        # 3. Create and switch to the new evaluation branch
        subprocess.run(["git", "checkout", "-b", current_branch_name], cwd=repo_path, check=True, capture_output=True, text=True, timeout=10)
        print(f"DEBUG: Created and checked out new branch {current_branch_name}")

        # 4. Apply the patch
        subprocess.run(["git", "apply", patch_path], cwd=repo_path, check=True, capture_output=True, text=True, timeout=10)
        print(f"✅ Patch aplicado en la rama {current_branch_name}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al aplicar el patch o gestionar ramas en {repo_path}:")
        print(f"STDOUT: {e.stdout.strip()}")
        print(f"STDERR: {e.stderr.strip()}")
        # Attempt to switch back to main to leave the repo in a cleaner state
        subprocess.run(["git", "checkout", "main"], cwd=repo_path, check=False, capture_output=True, text=True, timeout=10)
        return False
    except Exception as e:
        print(f"❗ Error inesperado al aplicar el patch en {repo_path}: {e}")
        return False
'''
def evaluate_patch(run_dir, issue_id, run_idx):
    stdout_path = os.path.join(run_dir, "stdout.txt")
    if not os.path.exists(stdout_path):
        print(f"❌ {stdout_path} no encontrado.")
        return False

    with open(stdout_path, "r") as f:
        content = f.read()

    if "🎉 Submission successful 🎉" not in content:
        print("❌ 'Submission successful' no encontrado en el log de SWE-agent.")
        return False
    else:
        print("🎉 Submission encontrado en el log de SWE-agent.")

    
    #patch_path = extract_patch_path(content)
    patch_path = extract_patch_path(content)
    if not patch_path or not os.path.isfile(patch_path):
        print(f"❌ El patch no es un archivo válido: {patch_path}")
        return False

    repo_path = "/Users/estebanm/Documents/C3Agent/C3Agent/pass@k/runs/Test_C3"
    if not apply_patch_to_repo(patch_path, repo_path, run_idx):
        return False

    # Detecta el lenguaje por el archivo editado más recientemente
    source_files = [f for f in os.listdir(repo_path) if f.endswith((".java", ".cpp"))]
    if not source_files:
        print("❌ No se encontraron archivos fuente reconocibles en el repositorio.")
        return False

    # Ordenar por tiempo de modificación descendente
    source_files.sort(key=lambda f: os.path.getmtime(os.path.join(repo_path, f)), reverse=True)
    edited_file = source_files[0]
    print(f"📝 Archivo modificado más recientemente: {edited_file}")

    if edited_file.endswith(".java"):
        return evaluate_java_patch(repo_path, issue_id)
    elif edited_file.endswith(".cpp"):
        return evaluate_cpp_patch(repo_path, issue_id)
    else:
        print(f"❌ Extensión no reconocida: {edited_file}")
        return False

def pass_at_k_by_first_success(success_list):
    """
    Retorna 1.0 si acierta en el primer intento,
    1/pos si acierta en la posición pos,
    0.0 si nunca acierta.
    """
    for i, success in enumerate(success_list, start=1):
        if success:
            return 1.0 / i
    return 0.0

def main():
    with open(PROBLEMS_FILE, "r") as f:
        problem_urls = [line.strip() for line in f if line.strip()]

    resultados = []

    for problem_url in problem_urls:
        issue_number = problem_url.split("/")[-1]
        problem_id = f"{issue_number}"        
        print(f"\n=============================")
        print(f"🏁 Ejecutando pruebas para issue #{problem_id}")
        print(f"=============================\n")

        success_list = []

        for i in range(RUNS_PER_TASK):
            run_dir = run_swe_agent(problem_url, i, f"issue{problem_id}")
            # Pass 'i' (run_idx) to evaluate_patch
            success = evaluate_patch(run_dir, f"{problem_id}", i)
            success_list.append(success)

            print(f"{run_dir}: {'✅ Correcto' if success else '❌ Incorrecto'}")

            if success:
                break  # Terminamos al primer éxito

        correct_count = 1 if any(success_list) else 0
        actual_attempts = len(success_list)
        pass_k = pass_at_k_by_first_success(success_list)

        print(f"\n✔️ Total correctos: {correct_count} / {actual_attempts}")
        print(f"📈 pass@k (by position) para issue #{problem_id}: {pass_k:.3f}\n")

        resultados.append({
            "issue": problem_id,
            "correctos": correct_count,
            "intentos": actual_attempts,
            "pass@k_by_first_success": round(pass_k, 3)
        })

    with open(CSV_OUTPUT, "w", newline="") as csvfile:
        fieldnames = ["issue", "correctos", "intentos", "pass@k_by_first_success"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in resultados:
            writer.writerow(row)

    total_issues = len(resultados)
    avg_pass_k = sum(row["pass@k_by_first_success"] for row in resultados) / total_issues
    perfect_ones = sum(1 for row in resultados if row["pass@k_by_first_success"] == 1.0)

    print("📊 Resultados finales:")
    print(f"📁 Issues evaluados: {total_issues}")
    print(f"📈 Promedio pass@k_by_first_success: {avg_pass_k:.3f}")
    print(f"🏅 Issues con pass@k = 1.0: {perfect_ones}")
    print(f"📝 Resultados guardados en: {CSV_OUTPUT}")

if __name__ == "__main__":
    main()