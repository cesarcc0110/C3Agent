import math
import asyncio
import httpx
import re
from asyncio import Semaphore

# ======================
# CONFIGURACIÓN
# ======================
OLLAMA_ENDPOINT = "{apikey}/v1/completions"
MODEL_NAME = "qwen2.5:7b"
TEMPERATURE = 0.8
MAX_TOKENS = 512
NUM_SAMPLES = 10
MAX_CONCURRENCY = 3

# PROMPT + TEST
PROMPT = "Fix the following Python function without including any additional text. It only returns the code: def suma(a, b):\n    "
TEST_CODE = "passed = suma(2, 3) == 5"

# ======================
# GENERACIÓN ASÍNCRONA
# ======================
sem = Semaphore(MAX_CONCURRENCY)

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
# MAIN
# ======================
async def main():
    samples = await generate_samples(PROMPT, NUM_SAMPLES)
    correct_count = sum(is_correct(extract_code(sample), TEST_CODE) for sample in samples)

    print("\nResultados individuales:")
    
    for i, sample in enumerate(samples, 1):
      clean_code = extract_code(sample)  # ✅ Extraer sin backticks
      print(f"Sample {i}:\n{clean_code}")
      if "Error" in sample:
        correct = False
      else:
        correct = is_correct(clean_code, TEST_CODE)
      print(f"Resultado: {'✅ Correcto' if correct else '❌ Incorrecto'}\n{'-'*40}")
      if correct:
        correct += 1



    passk = estimate_pass_at_k(len(samples), correct_count, k=NUM_SAMPLES)
    print(f"\n✅ Total correctas: {correct_count}/{NUM_SAMPLES}")
    print(f"📊 pass@{NUM_SAMPLES}: {passk:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
