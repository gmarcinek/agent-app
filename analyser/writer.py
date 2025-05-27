import os
import json
from pathlib import Path

def write_analysis(file_path: str, md_content: str, meta: dict):
    """
    Zapisuje pliki .analysis.md i .analysis.json do katalogu output/.meta
    z zachowaniem struktury folderów względem katalogu output/.

    Args:
        file_path: oryginalna ścieżka do pliku (np. output/app/src/App.tsx)
        md_content: zawartość pliku markdown do zapisu
        meta: słownik z metadanymi do zapisania w JSON
    """
    try:
        # Ścieżka względna względem "output"
        rel_path = Path(file_path).relative_to("output")
    except ValueError:
        # Jeśli file_path nie jest w output/, użyj pełnej nazwy
        rel_path = Path(file_path).name

    meta_dir = Path("output/.meta") / rel_path.parent
    os.makedirs(meta_dir, exist_ok=True)

    base_name = rel_path.name

    md_path = meta_dir / f"{base_name}.analysis.md"
    json_path = meta_dir / f"{base_name}.analysis.json"

    # Zapis markdown
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write(md_content)

    # Uzupełnij ścieżkę do summary w meta i zapisz json
    meta["summary_path"] = str(md_path)

    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(meta, f_json, indent=2, ensure_ascii=False)

    print(f"✅ Zapisano analizę:\n  - Markdown: {md_path}\n  - JSON: {json_path}")
