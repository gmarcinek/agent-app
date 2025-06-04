# agent/context/builder.py
import os
import json
from datetime import datetime
from agent.llm.use_llm import LLMClient

def build_hybrid_context(current_name: str, current_path: str, prompt_text: str = "", full_code: bool = False) -> str:
    """
    Buduje kontekst do prompta na podstawie:
    - current_path: dokładna ścieżka do aktualnego pliku (z scenario)
    - prompt_text: zadanie do wykonania
    - full_code: wymusza pełny kod (fallback)
    
    Głębokość powiązań: 1 (tylko bezpośrednie dependencies)
    """
    fragments = []
    
    # 1. AKTUALNY PLIK (pełny kod z dokładnej ścieżki)
    if os.path.exists(current_path):
        current_code = load_file_content(current_path)
        if current_code:
            fragments.append(f"### AKTUALNY PLIK: {current_path}\n{current_code}")
    
    # 2. POWIĄZANIA z knowledge.json (głębokość 1)
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
    
    # 3. KLUCZOWE PLIKI PROJEKTU (zawsze przydatne)
    key_files = get_key_project_files(knowledge)
    fragments.extend(key_files)
    
    return "\n\n".join(fragments) if fragments else ""


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
    
    # Znajdź klucz dla current_path w knowledge
    current_key = None
    for file_key, file_info in knowledge.get("files", {}).items():
        if file_info.get("meta", {}).get("path") == current_path:
            current_key = file_key
            break
    
    if not current_key:
        return []
    
    # Znajdź kto importuje current_key
    for file_key, deps in knowledge.get("dependencies", {}).items():
        if current_key in deps:
            file_path = knowledge.get("files", {}).get(file_key, {}).get("meta", {}).get("path")
            if file_path and file_path != current_path:  # nie siebie samego
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
    if not file_path or not file_path.startswith("output/"):
        return ""
    
    # output/app/src/components/Recipe1.tsx → output/.meta/app/src/components/Recipe1.tsx.analysis.md
    meta_path = file_path.replace("output/", "output/.meta/") + ".analysis.md"
    
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


def get_key_project_files(knowledge: dict) -> list[str]:
    """Zwraca informacje o kluczowych plikach projektu."""
    if not knowledge:
        return []
    
    key_fragments = []
    key_files = ["App.tsx", "package.json", "main.tsx", "index.html"]
    
    for file_key, file_info in knowledge.get("files", {}).items():
        file_path = file_info.get("meta", {}).get("path", "")
        
        if any(key_file in file_path for key_file in key_files):
            imports = file_info.get("meta", {}).get("imports", [])
            exports = file_info.get("meta", {}).get("exports", [])
            
            key_fragments.append(
                f"### KLUCZOWY PLIK: {file_path}\n"
                f"Importy: {', '.join(imports) if imports else 'brak'}\n"
                f"Eksporty: {', '.join(exports) if exports else 'brak'}"
            )
    
    return key_fragments
