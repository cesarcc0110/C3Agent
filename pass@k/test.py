import json
import os
import subprocess
import tempfile
import re

def detect_language(code_entry):
    code = code_entry.get("input", "") + code_entry.get("test", "")

    cpp_keywords = ['#include', 'std::', 'cin', 'cout', '->', '::', 'template']
    java_keywords = ['import java', 'public class', 'System.out']
    c_keywords = ['scanf', 'namespacePRINTF']

    if any(kw in code for kw in cpp_keywords) or "c++" in code_entry.get("input", "").lower():
        return 'cpp'
    elif any(kw in code for kw in java_keywords) or "java" in code_entry.get("input", "").lower():
        return 'java'
    elif any(kw in code for kw in c_keywords) or " c " in code_entry.get("input", "").lower():
        return 'c'
    else:
        return 'unknown'

def get_public_class_name(java_code: str) -> str:
    """
    Extrae el nombre de la clase pública del código Java.

    Args:
        java_code (str): El código fuente en Java como cadena de texto.

    Returns:
        str: El nombre de la clase pública si se encuentra, de lo contrario 'Main'.
    """
    match = re.search(r'public\s+class\s+(\w+)', java_code)
    if match:
        return match.group(1)
    return 'Main'

def run_csharp_test(code):
    with tempfile.TemporaryDirectory() as tmpdir:
        cs_file = os.path.join(tmpdir, "Test.cs")
        with open(cs_file, "w") as f:
            f.write(code)
        exe_file = os.path.join(tmpdir, "Test.exe")
        compile_cmd = ["csc", "-out:" + exe_file, cs_file]
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"❌ Compilation failed:\n{result.stderr}"
        run_result = subprocess.run([exe_file], capture_output=True, text=True)
        return run_result.stdout if run_result.returncode == 0 else f"❌ Runtime error:\n{run_result.stderr}"

def run_c_test(code):
    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = os.path.join(tmpdir, "test.c")
        exe_file = os.path.join(tmpdir, "test_exec")

        with open(c_file, "w") as f:
            f.write(code)

        # Compile
        compile_result = subprocess.run(["gcc", c_file, "-o", exe_file],
                                        capture_output=True, text=True)
        if compile_result.returncode != 0:
            return f"❌ Compilation failed:\n{compile_result.stderr}"

        # Run
        run_result = subprocess.run([exe_file], capture_output=True, text=True)
        if run_result.returncode != 0:
            return f"❌ Runtime error:\n{run_result.stderr}"
        return run_result.stdout if run_result.stdout.strip() else "⚠️ Executed successfully but no output."
    
def run_cpp_test(test_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.cpp")
        with open(file_path, "w") as f:
            f.write(test_code)

        exe_path = os.path.join(tmpdir, "test_exec")

        # Compilación
        compile_result = subprocess.run(
            ["g++", file_path, "-o", exe_path],
            capture_output=True, text=True
        )

        if compile_result.returncode != 0:
            return f"❌ Compilation failed:\n{compile_result.stderr}\n\nCode:\n{test_code}"

        # Ejecución
        run_result = subprocess.run(
            [exe_path],
            capture_output=True, text=True
        )

        if run_result.returncode != 0:
            return f"⚠️ Runtime error:\n{run_result.stderr}"

        if run_result.stdout.strip() == "":
            return "⚠️ Executed successfully but no output."
        
        return run_result.stdout

def run_java_test(test_code):
    with tempfile.TemporaryDirectory() as tmpdir:
        class_name = get_public_class_name(test_code)
        java_file = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_file, "w") as f:
            f.write(test_code)
        compile_result = subprocess.run(["javac", java_file], cwd=tmpdir, capture_output=True, text=True)
        if compile_result.returncode != 0:
            return f"❌ Compilation failed:\n{compile_result.stderr}"
        run_result = subprocess.run(["java", class_name], cwd=tmpdir, capture_output=True, text=True)
        return run_result.stdout

def run_tests_from_jsonl(jsonl_path):
    passed_tests = []
    failed_tests = []
    total_tests = 0

    with open(jsonl_path, "r") as f:
        for i, line in enumerate(f):
            entry = json.loads(line)
            test_code = entry.get("test", "")
            language = detect_language(entry)
            print(f"\n=== Test {i+1} | Language: {language.upper()} ===")

            if language == "cpp":
                result = run_cpp_test(test_code)
            elif language == "java":
                java_class_name = get_public_class_name(test_code)
                result = run_java_test(test_code)
            elif language == "c":
                result = run_c_test(test_code)
            else:
                result = "⚠️ Unsupported language or missing detection."

            print(result)
            total_tests += 1

            # Clasificación del resultado
            if "Test Case" in result and "Passed" in result:
                passed_tests.append((i + 1, result))
            elif "Test Case" in result and "Failed" in result:
                failed_tests.append((i + 1, result))
            elif result.strip().startswith("❌") or result.strip().startswith("⚠️"):
                failed_tests.append((i + 1, result))
            else:
                passed_tests.append((i + 1, result))  # Consideramos sin errores como éxito

    # Resumen final
    print("\n=== TEST SUMMARY ===")
    print(f"✅ Passed: {len(passed_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"🔢 Total: {total_tests}")

    if failed_tests:
        print("\n❌ Failed Test Details:")
        for test_num, output in failed_tests:
            print(f"- Test {test_num}:")

    if passed_tests:
        print("\n✅ Passed Test Details:")
        for test_num, output in passed_tests:
            print(f"- Test {test_num}")

# Llama a esta función con tu archivo JSONL
run_tests_from_jsonl("/Users/estebanm/Documents/C3Agent/C3Agent/pass@k/codealpaca_fix_subset.jsonl")