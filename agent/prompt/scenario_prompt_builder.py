import json
import os
from datetime import datetime
from agent.filesystem import FileSystem, get_flat_file_list_string
from registry.process_manager import ProcessManager


def build_scenario_prompt(goal: str, constraints: list[str], mode: str = "initial", intention: str = "mixed") -> str:
    """
    Buduje prompt do generowania scenariusza w trybie inicjalnym lub interaktywnym,
    z uwzględnieniem struktury plików i stanu dev servera.
    """
    process_manager = ProcessManager()
    constraints_txt = "\n".join(f"- {c}" for c in constraints) if constraints else "- Brak dodatkowych ograniczeń"

    fs = FileSystem(base_path="output")
    file_structure = fs.get_flat_file_list_string()

    # Wczytaj historię poprzednich kroków
    previous_steps = load_previous_steps()
    previous_steps_txt = format_previous_steps(previous_steps) if previous_steps else "Brak poprzednich kroków."

    # Context building based on intention
    if intention == "infrastructure":
        existing_context = "Kontekst pominięty - zadanie infrastrukturalne."
    else:
        existing_context = build_project_context(goal)

    # Sprawdź stan dev servera
    dev_server_status = ""
    if process_manager.is_dev_server_running:
        dev_server_status = "\n UWAGA: Dev server już działa - NIE dodawaj kroków uruchamiania dev servera!"
    else:
        dev_server_status = "\n Dev server nie działa - możesz go uruchomić na końcu scenariusza."
            
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
        mode_instructions = "\n\nZaplanuj kroki potrzebne do realizacji celu, nawet jeśli podobne były już próbowane wcześniej. Nie powtarzaj scaffoldera aplikacji."

    prompt = f"""
Jesteś agentem planującym działania kodującego agenta AI.

Masz za zadanie **KOMPLETNIE ZREALIZOWAĆ** cel: **{goal}**
{mode_instructions}

UWZGLĘDNIJ PONIŻSZE OGRANICZENIA:
{constraints_txt}

ISTNIEJĄCE KOMPONENTY I ICH FUNKCJONALNOŚĆ:
{existing_context}

OSTATNIO WYKONANE KROKI
{previous_steps_txt}

PRZYKŁAD KOMPLETNEGO PODEJŚCIA dla aplikacji z wieloma komponentami:
1. Setup projektu (mkdir, vite, npm install)
2. Instalacja dodatkowych zależności (np. react-router-dom)
3. Wygenerowanie WSZYSTKICH wymaganych komponentów (nie skracaj!)
4. Wygenerowanie komponentu głównego/listy z nawigacją
5. Modifikacja App.tsx z routingiem i integracją wszystkich komponentów
6. Uruchomienie dev servera (tylko jeśli nie działa już)

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
- "mkdir": {{ "path": "src/components" }}
- "delete": {{ "path": "output/obsolete.txt" }}
- "generate_code": {{
   "prompt": "bardzo dokładne i szczegółowe polecenie dla LLM co wygenerować, które uwzglęnia inne komponenty ze scenariusza oraz to co już istnieje, albo ma dopiero być budowane",
   "artifact": {{
     "name": "nazwa pliku",
     "path": "output/app/src/components/Foo.tsx",
     "extension": ".tsx"
   }}
 }}
 
PRZYKŁADY POPRAWNYCH KROKÓW:
{{
  "name": "Modyfikacja komponentu App",
  "type": "generate_code",
  "params": {{
    "prompt": "Zmodyfikuj komponent App w pliku App.tsx, aby wyświetlał aktualną godzinę...",
    "artifact": {{
      "name": "App.tsx",
      "path": "output/app/src/App.tsx",
      "extension": ".tsx"
    }}
  }}
}},
{{
  "name": "Instalacja zależności",
  "type": "run_script", 
  "params": {{
    "command": "npm install",
    "cwd": "output/app",
    "dev_server_mode": false
  }}
}}

Twoja odpowiedź **musi być poprawną tablicą JSON** zawierającą tylko obiekty kroków.
Zaczynaj od nawiasu `[` i kończ nawiasem `]`. Żadnych komentarzy ani tekstu poza listą.

{mode_instructions}
""".strip()

    log_scenario_prompt_to_file(goal, mode, prompt)

    return prompt


def build_project_context(goal: str) -> str:
    """Buduje kontekst istniejących komponentów"""
    try:
        from agent.context.builder import build_hybrid_context
        
        context = build_hybrid_context(
            prompt_text=goal,
        )
        
        return context if context and context.strip() else "Brak istniejących komponentów do analizy."
    except Exception as e:
        return f"Błąd podczas budowania kontekstu: {str(e)}"


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
    for i, step in enumerate(code_steps[-10:], 1):  # Ostatnie 10 kroków generate_code
        params = step.get('params', {})
        artifact = params.get('artifact', {})
        path = artifact.get('path', 'Nieznana ścieżka')
        prompt = params.get('prompt', 'Brak opisu')
        
        formatted_steps.append(f"{i}. {path}\n   Treść: {prompt}")
    
    return "\n".join(formatted_steps)

def log_scenario_prompt_to_file(goal: str, mode: str, prompt: str):
    """Loguje gotowy prompt scenariusza do pliku z timestampem."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"output/logs/scenario.{timestamp}.context.txt"
    
    # Upewnij się że katalog istnieje
    os.makedirs("output/logs", exist_ok=True)
    
    log_content = f"""=== SCENARIO PROMPT LOG ===
Timestamp: {datetime.now().isoformat()}
Goal: {goal}
Mode: {mode}
Prompt length: {len(prompt)} chars

=== FULL SCENARIO PROMPT ===
{prompt}

=== END OF SCENARIO PROMPT ===
"""
    
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_content)
    except Exception as e:
        print(f"Warning: Could not log scenario prompt to {log_path}: {e}")