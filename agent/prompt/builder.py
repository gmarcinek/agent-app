import textwrap
import os
from datetime import datetime
from agent.context.builder import build_hybrid_context

def build_prompt(prompt_text: str, artifact_name: str, artifact_path: str) -> str:
    """
    Buduje prompt dla LLM na podstawie:
    - prompt_text: główna treść zadania do wykonania
    - artifact_name: nazwa artefaktu (komponentu)
    - artifact_path: dokładna ścieżka do pliku z scenario
    """
    context = build_hybrid_context(
        current_path=artifact_path,
        prompt_text=prompt_text,
    )

    prompt = f"""
{prompt_text}

Poniżej znajduje się kontekst projektu:
{context or "Brak wcześniejszych komponentów."}

Wygeneruj kompletny plik dla artefaktu `{artifact_name}`.
Nie dodawaj żadnych komentarzy ani wyjaśnień.
""".strip()

    final_prompt = textwrap.dedent(prompt)
    
    # Logowanie gotowego prompta
    log_prompt_to_file(artifact_name, final_prompt)
    
    return final_prompt


def log_prompt_to_file(artifact_name: str, prompt: str):
    """Loguje gotowy prompt do pliku z timestampem."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"output/logs/{timestamp}.context.txt"
    
    # Upewnij się że katalog istnieje
    os.makedirs("output/logs", exist_ok=True)
    
    log_content = f"""=== PROMPT LOG FOR {artifact_name} ===
Timestamp: {datetime.now().isoformat()}
Artifact: {artifact_name}

=== FULL PROMPT ===
{prompt}

=== END OF PROMPT ===
"""
    
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)
    except Exception as e:
        print(f"Warning: Could not log prompt to {log_path}: {e}")