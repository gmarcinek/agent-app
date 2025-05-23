from agent.filesystem import FileSystem, get_flat_file_list_string

def build_scenario_prompt(goal: str, constraints: list[str], mode: str = "initial") -> str:
    """
    Buduje prompt do generowania scenariusza w trybie inicjalnym lub interaktywnym,
    z uwzględnieniem struktury plików.
    """
    constraints_txt = "\n".join(f"- {c}" for c in constraints) if constraints else "- Brak dodatkowych ograniczeń"

    fs = FileSystem(base_path="output")
    file_structure = fs.get_flat_file_list_string()
    print(f"📂 Struktura katalogu: {file_structure}")

    prompt = f"""
Jesteś agentem planującym działania kodującego agenta AI.

Masz za zadanie osiągnąć cel: **{goal}**
Uwzględnij poniższe ograniczenia:
{constraints_txt}

Struktura plików projektu:
{file_structure}

Każdy krok powinien mieć strukturę:
{{
  "name": "Nazwa kroku dla człowieka",
  "type": "typ_kroku",  // jeden z: generate_code, run_script, mkdir, delete
  "params": {{ ... }}   // parametry zależne od typu
}}

Dostępne typy kroków:
- "mkdir": {{ "path": "src/components" }}
- "run_script": {{ 
    "command": "npm install",
    "cwd": "output",
    "dev_server_mode": true | false // jeśli to skrypt uruchamiający dev server to niech nie blokuje terminala
  }} // zawsze działaj w obrębie cwd output lub głębiej
- "delete": {{ "path": "output/obsolete.txt" }}
- "generate_code": {{
    "prompt": "bardzo dokładne polecenie dla LLM co wygenerować",
    "artifact": {{
      "name": "nazwa pliku",
      "path": "output/src/components/Foo.tsx",
      "extension": ".tsx"
    }}
  }}

Twoja odpowiedź **musi być poprawną tablicą JSON** zawierającą tylko obiekty kroków.
Zaczynaj od nawiasu `[` i kończ nawiasem `]`. Żadnych komentarzy ani tekstu poza listą.
""".strip()

    if mode == "interactive":
        prompt += "\n\nZwróć tylko **nowe** kroki — nie powielaj już wykonanych ani nie zmieniaj istniejących."

    return prompt


def build_summary_prompt(state_json: str) -> str:
    """
    Buduje prompt do podsumowania aktualnego stanu agenta.
    """
    return f"""
Na podstawie poniższego stanu agenta i jego historii wygeneruj krótkie podsumowanie w 2–3 zdaniach.
Zakończ pytaniem: „Co dalej chcesz zbudować?”

Stan agenta:
{state_json}
""".strip()
