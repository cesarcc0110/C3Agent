import os
import subprocess
import csv
import json
import re

REPO_URL = "https://github.com/HeberM69/Test_C3"
CONFIG_PATH = "/Users/estebanm/Documents/C3Agent/SWE-agent/config/coding_challenge.yaml"
PROBLEMS_FILE = "problems.txt"
OUTPUT_BASE = "./runs"
RUNS_PER_TASK = 13
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

def extract_patch_path(content: str) -> str:
    """
    Extrae y limpia el PATCH_FILE_PATH desde un log.
    Elimina saltos de línea y espacios internos innecesarios.
    """
    match = re.search(r"PATCH_FILE_PATH='([^']+)'", content, re.DOTALL)
    if match:
        raw_path = match.group(1)
        # Elimina espacios nuevos y dobles (por si el path está mal formateado)
        cleaned_path = raw_path.replace("\n", "").replace(" ", "")
        return cleaned_path.strip()
    else:
        print("❌ No se encontró PATCH_FILE_PATH en el log.")
        return None

def evaluate_cpp_patch(repo_path, issue_id):
    test_input, expected_output = load_test_case(issue_id)
    if test_input is None:
        print(f"⚠️ No se encontró test para issue {issue_id}.")
        return False

    cpp_file = next((f for f in os.listdir(repo_path) if f.endswith(".cpp")), None)
    if not cpp_file:
        print("❌ No se encontró archivo .cpp")
        return False

    exe_path = os.path.join(repo_path, "solution_exec")
    compile_result = subprocess.run(
        ["g++", cpp_file, "-o", "solution_exec"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    if compile_result.returncode != 0:
        print("❌ Error al compilar C++:")
        print(compile_result.stderr)
        return False

    try:
        exec_result = subprocess.run(
            [exe_path],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=5
        )
        output = exec_result.stdout.strip()
        if output == expected_output.strip():
            print("✅ C++ Patch passed.")
            return True
        else:
            print(f"❌ Output incorrecto:\nEsperado: {expected_output}\nObtenido: {output}")
            return False
    except Exception as e:
        print(f"❗ Error ejecutando programa C++: {e}")
        return False
    
def evaluate_java_patch(repo_path, issue_id):
    import os

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

    # Guardar test como SolutionTest.java
    test_file_path = os.path.join(repo_path, "SolutionTest.java")
    with open(test_file_path, "w") as f:
        f.write(java_test_code)
    print("📝 Test JUnit guardado en SolutionTest.java")

    # Construir classpath
    classpath = build_junit_classpath()

    # Compilar todos los archivos .java
    try:
        compile_cmd = ["javac", "-cp", f".:{classpath}", "*.java"]
        compile_result = subprocess.run(
            compile_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if compile_result.returncode != 0:
            print("❌ Error al compilar los archivos Java:")
            print(compile_result.stderr)
            return False
    except Exception as e:
        print(f"❗ Excepción al compilar: {e}")
        return False

    # Ejecutar los tests con ConsoleLauncher desde Maven local
    try:
        test_cmd = [
            "java",
            "-cp", f".:{classpath}",
            "org.junit.platform.console.ConsoleLauncher",
            "--scan-class-path"
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

        if "Tests succeeded" in test_result.stdout:
            print("✅ Patch pasó todos los tests JUnit")
            return True
        else:
            print("❌ Alguno(s) de los tests fallaron")
            return False

    except Exception as e:
        print(f"❗ Excepción al ejecutar JUnit: {e}")
        return False
    
def apply_patch_to_repo(patch_path, repo_path, run_idx):
    # Create a unique branch name for each run attempt
    current_branch_name = f"{branch_name}issue{os.path.basename(repo_path).split('')[0]}_run{run_idx}"

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

    repo_path = os.path.join(run_dir, "repo")
    if not apply_patch_to_repo(patch_path, repo_path, run_idx):
        return False

    # Detecta el lenguaje según archivos en el repositorio
    files = os.listdir(repo_path)
    if any(f.endswith(".java") for f in files):
        return evaluate_java_patch(repo_path, issue_id)
    elif any(f.endswith(".cpp") for f in files):
        return evaluate_cpp_patch(repo_path, issue_id)
    elif os.path.exists(os.path.join(repo_path, "fixed.py")):
        test_input_str, expected_output_str = load_test_case(issue_id)
        patched_file = os.path.join(repo_path, "fixed.py")
        if not os.path.exists(patched_file):
            print(f"❌ No se encontró el archivo parcheado para ejecutar: {patched_file}")
            return False
        actual_output = execute_code_with_input(patched_file, test_input_str)
        if actual_output is None:
            return False
        return actual_output.strip() == expected_output_str.strip()
    else:
        print("❌ No se reconoce el lenguaje o archivo principal.")
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
        problem_id = f"issue{issue_number}"        
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