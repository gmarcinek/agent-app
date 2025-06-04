import json
import os
from agent.filesystem import FileSystem, get_flat_file_list_string

def build_scenario_prompt(goal: str, constraints: list[str], mode: str = "initial", registry=None) -> str:
   """
   Buduje prompt do generowania scenariusza w trybie inicjalnym lub interaktywnym,
   z uwzględnieniem struktury plików i stanu dev servera.
   """
   constraints_txt = "\n".join(f"- {c}" for c in constraints) if constraints else "- Brak dodatkowych ograniczeń"

   fs = FileSystem(base_path="output")
   file_structure = fs.get_flat_file_list_string()

   # Wczytaj historię poprzednich kroków
   previous_steps = load_previous_steps()
   previous_steps_txt = format_previous_steps(previous_steps) if previous_steps else "Brak poprzednich kroków."

   # Dodatkowe instrukcje w zależności od trybu
   mode_instructions = ""
   if mode == "initial":
       mode_instructions = """
KRYTYCZNE WYMAGANIA:
- Scenariusz musi być KOMPLETNY i zawierać WSZYSTKIE kroki do pełnej realizacji celu
- Jeśli cel wymienia konkretną liczbę elementów (np. 20), wygeneruj WSZYSTKIE
- NIE skracaj, NIE pomijaj elementów - wyczerpuj całe zadanie!
- Pamiętaj o modyfikacji głównych plików aplikacji (App.tsx) żeby używały nowych komponentów  
- Jeśli potrzebujesz routingu, zainstaluj react-router-dom
"""
   elif mode == "interactive":
       mode_instructions = "\n\nTryb interaktywny: Zwróć tylko **nowe** kroki — nie powielaj już wykonanych ani nie zmieniaj istniejących."

   prompt = f"""
Jesteś agentem planującym działania kodującego agenta AI.

Masz za zadanie **KOMPLETNIE ZREALIZOWAĆ** cel: **{goal}**
{mode_instructions}

UWZGLĘDNIJ PONIŻSZE OGRANICZENIA:
{constraints_txt}

STRUKTURA PLIKÓW PROJEKTU:
{file_structure}

OSTATNIO WYKONANE KROKI - START
{previous_steps_txt}
OSTATNIO WYKONANE KROKI - END

KAŻDY KROK POWINIEN MIEĆ STRUKTURĘ:
{{
 "name": "Nazwa kroku dla człowieka",
 "type": "typ_kroku",  // jeden z: generate_code, run_script, mkdir, delete
 "params": {{ ... }}   // parametry zależne od typu
}}

DOSTĘPNE TYPY KROKÓW:
- "run_script": {{ 
   "command": "npm install", // jeśli to dev serwer zawsze podawaj --port na którym ma się uruchomić
   "cwd": "output/app",      // zawsze działaj w obrębie cwd output lub głębiej
   "dev_server_mode": true | false
 }}
- "generate_code": {{
   "prompt": "bardzo dokładne i szczegółowe polecenie dla LLM co wygenerować",
   "artifact": {{
     "name": "nazwa pliku",
     "path": "output/app/src/components/Foo.tsx",
     "extension": ".tsx"
   }}
 }}

PRZYKŁAD KOMPLETNEGO PODEJŚCIA dla aplikacji z wieloma komponentami:
1. Setup projektu (mkdir, vite, npm install)
2. Instalacja dodatkowych zależności (np. react-router-dom)
3. Wygenerowanie WSZYSTKICH wymaganych komponentów (nie skracaj!)
4. Wygenerowanie komponentu głównego/listy z nawigacją
5. Modyfikacja App.tsx z routingiem i integracją wszystkich komponentów
6. Uruchomienie dev servera (tylko jeśli nie działa już)

Twoja odpowiedź **musi być poprawną tablicą JSON** zawierającą tylko obiekty kroków.
Zaczynaj od nawiasu `[` i kończ nawiasem `]`. Żadnych komentarzy ani tekstu poza listą.
""".strip()

   return prompt


def load_previous_steps() -> list:
    """
    Wczytuje poprzednie kroki z pliku scenario.json.
    Zwraca pustą listę jeśli plik nie istnieje lub jest nieprawidłowy.
    """
    scenario_path = "output/scenario.json"
    
    if not os.path.exists(scenario_path):
        return []
    
    try:
        with open(scenario_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Jeśli to lista kroków
            if isinstance(data, list):
                return data
            # Jeśli to obiekt z kluczem 'steps' lub podobnym
            elif isinstance(data, dict):
                return data.get('steps', data.get('scenario', []))
            else:
                return []
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return []


def format_previous_steps(steps: list) -> str:
    """
    Formatuje tylko kroki typu generate_code, pokazując ścieżkę i prompt.
    """
    if not steps:
        return "Brak poprzednich kroków."
    
    code_steps = [step for step in steps if step.get('type') == 'generate_code']
    
    if not code_steps:
        return "Brak poprzednich kroków typu generate_code."
    
    formatted_steps = []
    for i, step in enumerate(code_steps[-40:], 1):  # Ostatnie 40 kroków generate_code
        params = step.get('params', {})
        artifact = params.get('artifact', {})
        path = artifact.get('path', 'Nieznana ścieżka')
        prompt = params.get('prompt', 'Brak opisu')
        
        formatted_steps.append(f"{i}. {path}\n   Treść: {prompt}")
    
    return "\n".join(formatted_steps)


def build_summary_prompt(state_json: str) -> str:
   """
   Buduje prompt do podsumowania aktualnego stanu agenta.
   """
   return f"""
Na podstawie poniższego stanu agenta i jego historii wygeneruj krótkie podsumowanie w 2–3 zdaniach.
Skup się na tym co zostało zbudowane i jaki jest aktualny stan projektu.
Zakończ pytaniem: „Co dalej chcesz zbudować?"

Stan agenta:
{state_json}
""".strip()