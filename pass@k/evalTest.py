import math
import asyncio
import httpx
import re
from datasets import load_dataset
from asyncio import Semaphore

# ======================
# CONFIGURACIÓN
# ======================
OLLAMA_ENDPOINT = ""
MODEL_NAME = "qwen2.5:7b"
TEMPERATURE = 0.8
MAX_TOKENS = 512
NUM_SAMPLES = 10
MAX_CONCURRENCY = 3

# ======================
# DATASET DE HUGGINGFACE
# ======================
DATASET_NAME = "MadrigalJe/arcangel-BB"  # Cambia si quieres otro dataset
PROMPT_COLUMN = "input"
TEST_COLUMN = "output"

# ======================
# GENERACIÓN ASÍNCRONA
# ======================
sem = Semaphore(MAX_CONCURRENCY)

call_count = 0

async def generate_sample(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    try:
        async with sem:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(OLLAMA_ENDPOINT, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("choices", [{}])[0].get("text", "").strip()
    except httpx.HTTPStatusError as e:
        return f"Error HTTP: {e.response.status_code}"
    except httpx.ReadTimeout:
        return "Error: Timeout excedido"
    except Exception as e:
        return f"Error inesperado: {str(e)}"

async def generate_samples(prompt: str, k: int):
    print(f"Generando {k} muestras para el prompt:\n{prompt}\n{'=' * 40}")
    tasks = [generate_sample(prompt) for _ in range(k)]
    return await asyncio.gather(*tasks)

# ======================
# EVALUACIÓN
# ======================
def extract_code(text: str) -> str:
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def is_correct(sample: str, test_code: str) -> bool:
    try:
        namespace = {}
        exec(sample + "\n" + test_code, namespace)
        return namespace.get("passed", False)
    except Exception:
        return False

def estimate_pass_at_k(n: int, c: int, k: int) -> float:
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)

# ======================
# MAIN CORREGIDO PARA PARALLELIZAR
# ======================
K = 10
MAX_EXAMPLES = 100

async def evaluate_example(i, example):
    prompt = example[PROMPT_COLUMN]
    test_code = example[TEST_COLUMN][0] if isinstance(example[TEST_COLUMN], list) else example[TEST_COLUMN]

    if isinstance(prompt, list):
        prompt = prompt[0]

    generations = await generate_samples(prompt, K)

    correct = 0
    for gen in generations:
        clean_code = extract_code(gen)
        if is_correct(clean_code, test_code):
            correct += 1

    pass_k = estimate_pass_at_k(K, correct, k=1)
    print(f"Ejemplo {i+1}/{MAX_EXAMPLES} | Correctos: {correct}/{K} | pass@1: {pass_k:.3f}")
    return pass_k

async def main():
    dataset = load_dataset(DATASET_NAME, split="test")
    examples = dataset.select(range(min(MAX_EXAMPLES, len(dataset))))

    tasks = [evaluate_example(i, ex) for i, ex in enumerate(examples)]
    results = await asyncio.gather(*tasks)

    global_pass_k = sum(results) / len(results) if results else 0
    print(f"\n📊 pass@1 promedio sobre {len(results)} ejemplos: {global_pass_k:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
