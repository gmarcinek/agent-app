import os
from agent.validation.static import analyze_file
from agent.llm.use_llm import LLMClient

llm = LLMClient()

SUPPORTED_LINT_EXTENSIONS = [".tsx", ".ts", ".js", ".jsx", ".py", ".html"]

def strip_code_fences(text: str) -> str:
    lines = text.strip().splitlines()

    # Jeśli pierwsza linia to ``` (z językiem lub nie)
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()

def validate_and_recreate(prompt: str, filepath: str, extension: str, max_attempts: int = 5) -> tuple[str, dict]:
    """
    Próbuje wygenerować kod i poddaje go analizie statycznej, jeśli typ pliku to kod.
    Zwraca: (kod, raport_walidacji)
    """
    for attempt in range(1, max_attempts + 1):
        print(f"🧠 Generuję kod (podejście {attempt})...")

        try:
            raw_code = llm.chat(prompt)
            code = strip_code_fences(raw_code)
        except Exception as e:
            print(f"❌ Błąd LLM przy generowaniu kodu: {e}")
            continue

        # Zapis do tymczasowego pliku
        temp_path = filepath + ".tmp"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Pominięcie walidacji, jeśli rozszerzenie nie jest wspierane
        if extension.lower() not in SUPPORTED_LINT_EXTENSIONS:
            os.remove(temp_path)
            return code, {
                "ok": True,
                "details": f"Brak analizy statycznej dla rozszerzenia '{extension}'."
            }

        # Walidacja statyczna
        ok, report = analyze_file(temp_path)
        os.remove(temp_path)

        if ok:
            return code, {"ok": True, "details": report}

        print(f"⚠️  Walidacja nieudana:\n{report.strip()}")

    # Jeśli wszystkie próby zawiodły
    return code, {"ok": False, "details": report}
