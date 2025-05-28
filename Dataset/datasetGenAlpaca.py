import json
import random
from datasets import load_dataset

def process_codealpaca(output_path="codehumaneval.jsonl", max_samples=1000):  # Cambiado de 3500 a 1100
    dataset = load_dataset(
        "THUDM/humaneval-x",
        name="cpp",
        split="test",
        trust_remote_code=True  # <- necesario para que funcione
    )
    filtered = [
        ex for ex in dataset
        if any(kw in ex["prompt"].lower() for kw in ["fix", "bug", "error", "debug", "edit", "modify", "change", "give ", "write ", "create ", "implement ", "develop ", "produce ", "construct ", "build ", "formulate ", "generate ", "establish"])
    ]

    # Barajar y tomar muestra aleatoria
    random.seed(42)
    sampled = random.sample(filtered, min(max_samples, len(filtered)))

    with open(output_path, "w") as f:
        for example in sampled:
            entry = {
                "instruction": example["prompt"].strip(),
                "input": example["declaration"].strip(),
                "output": example["canonical_solution"].strip(),
                "test": example["test"].strip()
            }
            f.write(json.dumps(entry) + "\n")
    print(f"[✓] Saved: {output_path} ({len(sampled)} samples)")

# === Ejecutar ===
if __name__ == "__main__":
    process_codealpaca()  # Ahora usará 1100 directamente