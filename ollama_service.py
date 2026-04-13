# ollama_service.py

import json
import re
import requests
from validator import validate_row

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def build_prompt(df, n):
    sample = df.sample(min(2, len(df))).to_dict(orient="records")

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

Here are 2 real rows to learn from:
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


def generate_rows(df, n):
    print("=" * 50)
    print(f"Generating {n} rows")
    print("=" * 50)

    all_rows = []
    max_attempts = n * 3
    attempts = 0
    i = 0

    while len(all_rows) < n and attempts < max_attempts:

        print(f"Generating row {len(all_rows)+1}/{n}...")

        try:
            prompt = build_prompt(df, 1)
            raw = call_ollama(prompt)

            row = clean_json(raw)

            if isinstance(row, list):
                row = row[0]

            is_valid, result = validate_row(row, df)

            if is_valid:
                all_rows.append(result)
                print(f"Accepted ({len(all_rows)}/{n})")
            else:
                print(f"Rejected: {result}")

        except Exception as e:
            print(f"Error: {e}")

        attempts += 1
        i += 1

    print(f"\nFinal: {len(all_rows)} valid rows")

    return all_rows, []
