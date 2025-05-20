import json
import random
from datasets import load_dataset

# === QuixBugs ===
def process_quixbugs(output_path="quixbugs_instruction.jsonl"):
    dataset = load_dataset("Muennighoff/quixbugs", split="train")
    with open(output_path, "w") as f:
        for example in dataset:
            instruction = "Fix the following buggy program: " + example["docstring"]
            input_code = example["buggy_program"]
            output_code = example["solution"]
            entry = {
                "instruction": instruction.strip(),
                "input": input_code.strip(),
                "output": output_code.strip()
            }
            f.write(json.dumps(entry) + "\n")
    print(f"[✓] Saved: {output_path} ({len(dataset)} samples)")

def process_codealpaca(output_path="codealpaca_fix_subset.jsonl", max_samples=1000):  # Cambiado de 3500 a 1100
    dataset = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
    filtered = [ex for ex in dataset if any(kw in ex["instruction"].lower() for kw in ["fix", "bug", "error", "debug", "edit", "modify", "change"])]

    # Barajar y tomar muestra aleatoria
    random.seed(42)
    sampled = random.sample(filtered, min(max_samples, len(filtered)))

    with open(output_path, "w") as f:
        for example in sampled:
            entry = {
                "instruction": example["instruction"].strip(),
                "input": example.get("input", "").strip(),
                "output": example["output"].strip()
            }
            f.write(json.dumps(entry) + "\n")
    print(f"[✓] Saved: {output_path} ({len(sampled)} samples)")

# === Fusionar datasets ===
def merge_jsonl_files(file1, file2, output_path="dataset.jsonl"):
    count = 0
    with open(output_path, "w") as out_file:
        for file_path in [file1, file2]:
            with open(file_path, "r") as in_file:
                for line in in_file:
                    out_file.write(line)
                    count += 1
    print(f"[✓] Dataset fusionado guardado en: {output_path} ({count} samples)")

# === Ejecutar ===
if __name__ == "__main__":
    process_quixbugs()
    process_codealpaca()  # Ahora usará 1100 directamente
    merge_jsonl_files("quixbugs_instruction.jsonl", "codealpaca_fix_subset.jsonl")