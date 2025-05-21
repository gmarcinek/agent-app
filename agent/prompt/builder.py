import textwrap
from agent.context.builder import build_hybrid_context

def build_prompt(prompt_text: str, artifact_name: str, context_mode: str = "meta_only") -> str:
    """
    Buduje prompt dla LLM na podstawie:
    - prompt_text: główna treść zadania do wykonania
    - artifact_name: nazwa artefaktu (komponentu)
    - context_mode: czy dołączyć pełny kod poprzednich komponentów czy tylko meta
    """
    context = build_hybrid_context(
        current_name=artifact_name,
        full_code=(context_mode == "full_code")
    )

    prompt = f"""
{prompt_text}

Poniżej znajduje się kontekst projektu:
{context or "Brak wcześniejszych komponentów."}

Wygeneruj kompletny plik dla artefaktu `{artifact_name}`.
Nie dodawaj żadnych komentarzy ani wyjaśnień.
""".strip()

    return textwrap.dedent(prompt)
