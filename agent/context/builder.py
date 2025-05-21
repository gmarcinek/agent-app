import os
import json

def build_hybrid_context(current_name: str, full_code: bool = False) -> str:
    """
    Buduje kontekst do prompta na podstawie poprzednich komponentów.
    - Jeśli full_code = True → dołącza kod .tsx
    - Jeśli False → tylko metadane
    """
    context_dir = "output/context"
    if not os.path.exists(context_dir):
        return ""

    fragments = []

    for filename in os.listdir(context_dir):
        if not filename.endswith(".meta.json"):
            continue

        with open(os.path.join(context_dir, filename), encoding="utf-8") as f:
            meta = json.load(f)

        if meta["name"] == current_name:
            continue  # pomijamy bieżący artefakt

        if full_code:
            try:
                with open(meta["path"], encoding="utf-8") as code_file:
                    code = code_file.read()
                fragments.append(f"### {meta['name']} ({meta['path']})\n{code}")
            except Exception as e:
                fragments.append(f"### {meta['name']} (BŁĄD ODCZYTU KODU): {e}")
        else:
            fragments.append(f"- {meta['name']}: {meta['path']} ({meta['extension']})")

    return "\n\n".join(fragments)
