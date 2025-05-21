import os
import re
import json
from agent.input import AgentInput
from agent.llm.use_llm import LLMClient

def plan_scenario(agent_input: AgentInput) -> list[dict]:
    llm = LLMClient(model="gpt-4o")

    prompt = f"""
Twoim zadaniem jest zaplanowanie sekwencji działań, jakie powinien wykonać agent kodujący,
aby osiągnąć cel: "{agent_input.goal}"

Uwzględnij poniższe ograniczenia:
{"\n".join(f"- {c}" for c in agent_input.constraints)}

Każdy krok powinien być obiektem o strukturze:

{{
  "prompt": "bardzo konkretny i dokładny opis tego, co ma zrobić LLM (np. napisz komponent ...)",
  "artifact": {{
    "name": "nazwa_komponentu",
    "path": "output/components/Nazwa.tsx",
    "extension": ".tsx"
  }}
}}

WAŻNE: Twoja odpowiedź MUSI zaczynać się od znaku '[' i kończyć znakiem ']'.
Odpowiedź musi być poprawną tablicą JSON bez żadnego tekstu przed lub po nawiasach.
"""

    try:
        content = llm.chat(prompt)

        os.makedirs("logs", exist_ok=True)
        with open("logs/plan_raw_response.txt", "w", encoding="utf-8") as f:
            f.write(content)

        # 🧠 Ekstrakcja JSON przez indeksy lub regex
        try:
            # 1. podejście: find() na nawiasach
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx == -1 or end_idx <= start_idx:
                raise ValueError("Brak nawiasów w odpowiedzi")

            json_text = content[start_idx:end_idx]
            with open("logs/plan_extracted_json.txt", "w", encoding="utf-8") as f:
                f.write(json_text)

            steps = json.loads(json_text)
            if not isinstance(steps, list):
                raise ValueError("Odpowiedź LLM nie jest listą kroków.")

            with open("logs/plan_parsed.json", "w", encoding="utf-8") as f:
                json.dump(steps, f, indent=2, ensure_ascii=False)

            return steps

        except (json.JSONDecodeError, ValueError) as e:
            # 2. fallback: regex na całość
            match = re.search(r'\[[\s\S]*\]', content)
            if not match:
                raise ValueError(f"Nie znaleziono poprawnej tablicy JSON: {e}")

            json_text = match.group(0)
            with open("logs/plan_regex_extracted.txt", "w", encoding="utf-8") as f:
                f.write(json_text)

            steps = json.loads(json_text)
            if not isinstance(steps, list):
                raise ValueError("Po regexie: wynik nie jest listą kroków.")

            return steps

    except Exception as e:
        preview = content[:150] + ("..." if len(content) > 150 else "") if 'content' in locals() else "[BRAK]"
        raise RuntimeError(f"❌ Błąd podczas planowania:\n{e}\n🪵 Podgląd:\n{preview}")
