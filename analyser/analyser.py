import os
import json
from pathlib import Path
from analyser.writer import write_analysis
from analyser.tree_parser import parse_code_file
from agent.llm.use_llm import LLMClient
from dotenv import load_dotenv
from analyser.constants import LANGUAGE_MAP

load_dotenv()

def detect_language(path: str) -> str:
    """Mapowanie rozszerzeń na języki dla tree-sitter"""
    ext = Path(path).suffix.lower()

    if ext in LANGUAGE_MAP:
        return LANGUAGE_MAP[ext]

    filename = Path(path).name.lower()
    if filename in ["dockerfile", "makefile", "rakefile", "gemfile"]:
        return filename.replace("file", "")

    return "text"

def build_summary_prompt(language: str, content: str) -> str:
    content_sample = content[:2000]

    if language in ["json", "yaml", "toml", "xml"]:
        return (
            f"Opisz, co ustawia ten plik konfiguracyjny ({language}). "
            "Wskaż najważniejsze sekcje i parametry oraz ich wpływ na działanie aplikacji. "
            "Bez ogólników ani zgadywania. Maksymalnie 3 konkretne zdania.\n\n"
            f"{content_sample}"
        )

    elif language in ["md", "rst", "txt"]:
        return (
            "Streść temat i przeznaczenie tego dokumentu. "
            "Skup się na konkretach, nie cytuj i nie parafrazuj tytułów. "
            "Maksymalnie 3 krótkie, rzeczowe zdania.\n\n"
            f"{content_sample}"
        )

    elif language == "gitignore":
        return None

    else:
        return (
            f"Opisz, co robi ten kod źródłowy ({language}). "
            "Opisz efekt działania — co realizuje, jakie elementy udostępnia, co osiąga. "
            "Wymień najważniejsze funkcje, klasy lub komponenty, ale bez opisywania ich wewnętrznej implementacji. "
            "Nie podawaj nazw pliku, nie zgaduj, nie opisuj importów ani oczywistości. "
            "Zacznij każde zdanie od czasownika. Styl: precyzyjny, zwięzły. Maksymalnie 10 zdań.\n\n"
            f"{content_sample}"
        )

def build_md_content(path: str, meta: dict, summary: str) -> str:
    """
    Buduje zawartość pliku .md z podsumowaniem, importami i eksportami.
    Nie zawiera kodu ani danych technicznych typu liczba tokenów.
    """
    parts = [f"# Plik: {path}", ""]

    parts.append("## Podsumowanie")
    parts.append(summary.strip())
    parts.append("")

    imports = meta.get("imports", [])
    if imports:
        external = sorted([i for i in imports if not i.startswith(('.', '..'))])
        local = sorted([i for i in imports if i.startswith(('.', '..'))])

        parts.append("## Importy")
        parts.extend([f"- {imp}" for imp in external + local])
        parts.append("")

    exports = meta.get("exports", [])
    if exports:
        parts.append("## Eksporty")
        parts.extend([f"- {exp}" for exp in exports])
        parts.append("")

    return "\n".join(parts)

async def analyze_file(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️ Nie mogę otworzyć {path}: {e}")
        return

    language = detect_language(path)

    if len(content) > 100000:
        print(f"⚠️ Plik {path} jest za duży dla analizy ({len(content)} znaków)")
        return

    parsed_data = parse_code_file(content, language)

    prompt = build_summary_prompt(language, content)

    if language == "gitignore" or prompt is None:
        summary = "Plik jest ignorowany (np. .gitignore) lub nie wymaga podsumowania."
    else:
        llm = LLMClient(model="gpt-4o-mini")
        try:
            summary = llm.chat(prompt).strip()
        except Exception as e:
            print(f"❌ Błąd LLM dla {path}: {e}")
            summary = f"Plik {language} ({len(content.splitlines())} linii)"

    meta = {
        "path": path,
        "language": language,
        "type": parsed_data.get("type", "unknown"),
        "tokens": len(content.split()),
        "lines": len(content.splitlines()),
        "size_bytes": len(content.encode("utf-8")),
        "imports": parsed_data.get("imports", []),
        "exports": parsed_data.get("exports", []),
        "summary_path": None,
        "embedding_ref": None,
    }

    md_content = build_md_content(path, meta, summary)

    write_analysis(path, md_content, meta)
    print(f"✅ Przeanalizowano: {path} ({meta['type']}, {len(meta['imports'])} importów, {len(meta['exports'])} eksportów)")
