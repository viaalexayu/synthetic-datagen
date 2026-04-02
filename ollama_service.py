# ollama_service.py

import json
import re
import requests
from validator import validate_row

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"
BATCH_SIZE = 3


def build_prompt(df, n):
    sample = df.sample(min(5, len(df))).to_dict(orient="records")

    prompt = f"""You are a BGP network dataset generator.
Return ONLY a valid JSON array of exactly {n} new rows. No explanation, no markdown fences.

Column rules:
- category: one of ["origin_change", "prepend", "forged_as_path", "typo"]
- hj_as: list of ASN strings e.g. ["12345"]
- hj_pfx: IP prefix string e.g. "192.168.1.0/24"
- vt_as: integer
- vt_pfx: IP prefix string
- propagation: float 0.0 to 1.0
- is_moas: 0 or 1
- moas_duration: float or null
- is_submoas: 0 or 1
- submoas_duration: float or null
- diff_cider: float or null
- global_hege_freq_hijacked: float 0.0 to 1.0
- global_hege_freq_normal: float
- local_hege_hijacker: float
- local_hege_freq_hijacked: float 0.0 to 1.0
- local_hege_freq_normal: float 0.0 to 1.0
- edit_distance: integer 1 to 4
- prepending: float 0.0 to 1.0
- local_similarity: float 0.0 to 1.0
- local_hege_freq: float 0.0 to 1.0
- global_hege_freq: float 0.0 to 1.0
- local_union: float 0.0 to 1.0
- hege_score: nested JSON string like "{{}}"
- title: unique string like "event_name_N.pickle"

Here are 5 real rows to learn from:
{json.dumps(sample, indent=2)}

Generate exactly {n} new rows. Vary categories. Make every title unique.
Return ONLY the raw JSON array starting with [ and ending with ]."""

    return prompt


def fix_single_quotes(text):
    """Replaces single-quoted string values with double-quoted ones."""
    result = re.sub(
        r":\s*'(.*?)'(\s*[,\}\]])",
        lambda m: ': "' + m.group(1).replace('"', '\\"') + '"' + m.group(2),
        text,
        flags=re.DOTALL
    )
    return result


def clean_json(raw):
    """
    Tries multiple strategies to extract valid JSON
    from a messy LLaMA response.
    """

    # strategy 1 — strip markdown fences
    raw = re.sub(r"```json|```", "", raw).strip()

    # strategy 2 — find the array boundaries
    start = raw.find("[")
    end = raw.rfind("]") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON array found in response")

    raw = raw[start:end]

    # strategy 3 — fix single quotes
    raw = fix_single_quotes(raw)

    # strategy 4 — try parsing as-is
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # strategy 5 — truncated array, find last complete object
    last_complete = raw.rfind("},")
    if last_complete == -1:
        last_complete = raw.rfind("}")
    if last_complete != -1:
        fixed = raw[:last_complete + 1] + "\n]"
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    # strategy 6 — remove trailing commas
    fixed = re.sub(r",\s*([}\]])", r"\1", raw)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ValueError("Could not repair JSON from LLaMA response")


def call_ollama(prompt):
    """Makes a single request to Ollama and returns raw text."""
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=300)

    if response.status_code != 200:
        raise Exception(f"Ollama returned status {response.status_code}")

    return response.json()["response"]


def generate_batch(df, batch_size):
    """
    Generates one small batch of rows.
    Returns whatever rows it can — skips bad batches silently.
    """
    try:
        prompt = build_prompt(df, batch_size)
        raw = call_ollama(prompt)
        print(f"  Batch response (first 300 chars): {raw[:300]}")
        return clean_json(raw)
    except Exception as e:
        print(f"  Batch failed: {e}")
        return []


def generate_rows(df, n):
    """
    Keeps calling LLaMA in small batches of BATCH_SIZE
    until we collect exactly n valid rows or run out of attempts.

    Example: n=10, BATCH_SIZE=3
      Batch 1 → asks for 3, gets 3  (total: 3/10)
      Batch 2 → asks for 3, gets 2  (total: 5/10)
      Batch 3 → asks for 3, gets 3  (total: 8/10)
      Batch 4 → asks for 2, gets 2  (total: 10/10) done!
    """
    print("=" * 50)
    print(f"Generating {n} rows in batches of {BATCH_SIZE}")
    print("=" * 50)

    all_rows = []
    max_attempts = n * 3  # try up to 3x requested to handle failed batches
    attempts = 0
    batch_num = 1

    while len(all_rows) < n and attempts < max_attempts:
        remaining = n - len(all_rows)
        batch_size = min(BATCH_SIZE, remaining)

        print(f"Batch {batch_num}: requesting {batch_size} rows "
              f"({len(all_rows)}/{n} collected so far)...")

        batch = generate_batch(df, batch_size)
        print(f"Batch {batch_num}: got {len(batch)} rows back")

        all_rows.extend(batch)
        attempts += batch_size
        batch_num += 1

    print(f"Total rows collected from LLaMA: {len(all_rows)}")

    # validate every row
    valid_rows = []
    rejected_rows = []

    for row in all_rows:
        is_valid, result = validate_row(row, df)
        if is_valid:
            valid_rows.append(result)
        else:
            rejected_rows.append({"row": row, "reason": result})

    # trim to exactly n if we collected more
    valid_rows = valid_rows[:n]

    print(f"Valid: {len(valid_rows)} | Rejected: {len(rejected_rows)}")
    print("=" * 50)

    return valid_rows, rejected_rows
