import os
import json
from datetime import datetime

def build_hybrid_context(current_path: str = None, prompt_text: str = "") -> str:
    """
    Buduje kontekst do prompta na podstawie:
    - current_path: dokładna ścieżka do aktualnego pliku (opcjonalne)
    - prompt_text: zadanie do wykonania
    
    Głębokość powiązań: 1 (tylko bezpośrednie dependencies)
    """
    fragments = []
    
    # 1. STRUKTURA PROJEKTU (zawsze przydatna)
    project_tree = get_project_tree("output/app")
    if project_tree:
        fragments.append(f"### STRUKTURA PROJEKTU:\n{project_tree}")
    
    # 2. AKTUALNY PLIK (pełny kod z dokładnej ścieżki) - OPCJONALNIE
    if current_path and os.path.exists(current_path):
        current_code = load_file_content(current_path)
        if current_code:
            fragments.append(f"### AKTUALNY PLIK: {current_path}\n{current_code}")
    
    # 3. POWIĄZANIA z knowledge.json (głębokość 1) - tylko jeśli mamy current_path
    if current_path:
        knowledge = load_knowledge_graph("output/.synth/knowledge.json")
        if knowledge:
            # Parents - kto importuje current_file
            parents = find_parents(current_path, knowledge)
            for parent_file in parents:
                analysis = load_full_analysis(parent_file)
                if analysis:
                    fragments.append(f"### UŻYWA TEGO PLIKU: {parent_file}\n{analysis}")
            
            # Children - co current_file importuje  
            children = find_children(current_path, knowledge)
            for child_file in children:
                analysis = load_full_analysis(child_file)
                if analysis:
                    fragments.append(f"### IMPORTOWANY PRZEZ TEN PLIK: {child_file}\n{analysis}")

    return "\n\n".join(fragments) if fragments else ""


def get_project_tree(root_path: str) -> str:
    """Generuje drzewo plików projektu (tylko istotne pliki)"""
    if not os.path.exists(root_path):
        return ""
    
    tree_lines = []
    
    # Lista rozszerzeń które nas interesują
    relevant_extensions = {'.tsx', '.ts', '.jsx', '.js', '.json', '.html', '.css', '.md'}
    # Katalogi do pominięcia
    skip_dirs = {'.git', 'node_modules', '.meta', '.synth', 'dist', 'build', '.vscode'}
    
    for root, dirs, files in os.walk(root_path):
        # Filtruj katalogi
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        # Filtruj i sortuj pliki
        relevant_files = []
        for file in files:
            if (not file.startswith('.') and 
                any(file.endswith(ext) for ext in relevant_extensions)):
                relevant_files.append(file)
        
        # Dodaj pliki do drzewa
        for file in sorted(relevant_files):
            full_path = os.path.join(root, file)
            # Konwertuj na relative path od output/
            rel_path = os.path.relpath(full_path, "output").replace("\\", "/")
            tree_lines.append(f"output/{rel_path}")
    
    return "\n".join(tree_lines)


def load_knowledge_graph(knowledge_path: str) -> dict:
    """Wczytuje knowledge.json z obsługą błędów."""
    if not os.path.exists(knowledge_path):
        return {}
    
    try:
        with open(knowledge_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return {}


def find_parents(current_path: str, knowledge: dict) -> list[str]:
    """Znajduje pliki które importują current_path (głębokość 1)."""
    parents = []
    
    # Normalizuj separatory  
    normalized_current = current_path.replace("/", "\\")
    
    # Znajdź klucz dla current_path
    current_key = None
    for file_key, file_info in knowledge.get("files", {}).items():
        if file_info.get("meta", {}).get("path") == normalized_current:
            current_key = file_key
            break
    
    if not current_key:
        return []
    
    # Znajdź dependency_string który mapuje na current_key
    current_filename = os.path.basename(normalized_current)  # App.tsx
    possible_deps = [f"./{current_filename}", f"../{current_filename}"]  # ./App.tsx, ../App.tsx
    
    # Szukaj kto ma dependency na current_file
    for file_key, deps in knowledge.get("dependencies", {}).items():
        for dep in deps:
            if dep in possible_deps:  # ./App.tsx
                file_path = knowledge.get("files", {}).get(file_key, {}).get("meta", {}).get("path")
                if file_path and file_path != normalized_current:
                    parents.append(file_path)
    
    return parents


def find_children(current_path: str, knowledge: dict) -> list[str]:
    """Znajduje pliki które current_path importuje (głębokość 1)."""
    children = []
    
    # Znajdź klucz dla current_path w knowledge
    current_key = None
    for file_key, file_info in knowledge.get("files", {}).items():
        if file_info.get("meta", {}).get("path") == current_path:
            current_key = file_key
            break
    
    if not current_key:
        return []
    
    # Znajdź co current_key importuje
    deps = knowledge.get("dependencies", {}).get(current_key, [])
    for dep_key in deps:
        file_path = knowledge.get("files", {}).get(dep_key, {}).get("meta", {}).get("path")
        if file_path and file_path != current_path:  # nie siebie samego
            children.append(file_path)
    
    return children


def load_full_analysis(file_path: str) -> str:
    """Ładuje pełną analizę .md dla pliku."""
    if not file_path or not file_path.startswith("output"):
        return ""
    
    # Normalizuj separatory PRZED replace (Windows używa \)
    normalized_path = file_path.replace("\\", "/")
    
    # output/app/src/main.tsx → output/.meta/app/src/main.tsx.analysis.md
    meta_path = normalized_path.replace("output/", "output/.meta/") + ".analysis.md"
    
    # Konwertuj z powrotem na separatory systemu
    meta_path = meta_path.replace("/", os.sep)
    
    if os.path.exists(meta_path):
        try:
            with open(meta_path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    return ""


def load_file_content(file_path: str) -> str:
    """Wczytuje zawartość dowolnego pliku."""
    if not os.path.exists(file_path):
        return ""
    
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""