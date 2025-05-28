import json
import time
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from constants.constants import (
    LANGUAGE_MAP, TEXT_EXTENSIONS, COMMON_TEXT_FILES
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = Path(__file__).parent / "synth_config.json"
OUTPUT_DIR = ROOT / "output"
META_DIR = OUTPUT_DIR / ".meta"
SYNTH_DIR = OUTPUT_DIR / ".synth"
OUTPUT_FILE = SYNTH_DIR / "knowledge.json"

# Wczytaj konfigurację
def load_config():
    config = {
        "index_weight": 0.2
    }
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open() as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"⚠️ Nieprawidłowy config: {e}", file=sys.stderr)
    return config

CONFIG = load_config()

def is_valid(path: Path) -> bool:
    """
    W synthetiser obserwujemy tylko .meta/ więc przyjmujemy wszystkie .json pliki
    (poza node_modules dla bezpieczeństwa)
    """
    print(f"🔍 Sprawdzam: {path}")
    print(f"  - suffix: {path.suffix}")
    print(f"  - is_file: {path.is_file()}")
    print(f"  - node_modules check: {'node_modules' not in str(path)}")
    
    result = (
        path.suffix == ".json"
        and "node_modules" not in str(path)
        and path.is_file()
    )
    print(f"  - WYNIK: {result}")
    return result

# Metadane pliku
def assign_weight(file_path: str) -> float:
    if "index." in Path(file_path).name:
        return CONFIG.get("index_weight", 0.2)
    return 1.0

def infer_language(file_path: str) -> tuple[str | None, str, bool]:
    suffix = Path(file_path).suffix.lower()
    name = Path(file_path).stem
    language = LANGUAGE_MAP.get(suffix)
    is_text = suffix in TEXT_EXTENSIONS or name in COMMON_TEXT_FILES
    return language, suffix, is_text

def safe_load_json(path: Path):
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ Wczytano JSON z {path}: {list(data.keys())}")
            return data
    except Exception as e:
        print(f"❌ Błąd w pliku {path}: {e}", file=sys.stderr)
        return None

# Przetwarzanie pojedynczego pliku
def update_file_entry(path: Path, files_data: dict, dependencies: dict, symbols_index: dict):
    print(f"🔧 Przetwarzam: {path}")
    
    if not is_valid(path):
        print(f"❌ Plik odrzucony przez is_valid: {path}")
        return

    rel_path = str(path.relative_to(META_DIR))
    print(f"📁 Względna ścieżka: {rel_path}")
    
    data = safe_load_json(path)
    if data is None:
        print(f"❌ Nie udało się wczytać JSON: {path}")
        return

    lang, ext, is_text = infer_language(rel_path)
    print(f"🔤 Język: {lang}, rozszerzenie: {ext}, tekst: {is_text}")

    files_data[rel_path] = {
        "meta": data,
        "weight": assign_weight(rel_path),
        "language": lang,
        "extension": ext,
        "text": is_text
    }

    dependencies[rel_path] = data.get("imports", [])
    print(f"📦 Zależności: {dependencies[rel_path]}")

    exports = data.get("exports", [])
    for symbol in exports:
        symbols_index[symbol] = {
            "file": rel_path,
            "type": "export"
        }
    print(f"📤 Eksporty: {exports}")
    
    print(f"✅ Dodano do knowledge: {rel_path}")

# Całościowa inicjalizacja
def synthesise_all():
    if not META_DIR.exists():
        print("⏳ Oczekiwanie na folder .meta...")
        return

    print(f"📂 Szukam plików w: {META_DIR}")
    json_files = list(META_DIR.rglob("*.json"))
    print(f"🔍 Znaleziono {len(json_files)} plików JSON:")
    for f in json_files:
        print(f"  - {f}")

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)

    files_data, dependencies, symbols_index = {}, {}, {}

    for json_file in json_files:
        update_file_entry(json_file, files_data, dependencies, symbols_index)

    print(f"📊 Podsumowanie:")
    print(f"  - Pliki: {len(files_data)}")
    print(f"  - Zależności: {len(dependencies)}")
    print(f"  - Symbole: {len(symbols_index)}")

    output = {
        "files": files_data,
        "dependencies": dependencies,
        "symbols": symbols_index
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        print(f"🧠 Wygenerowano: {OUTPUT_FILE}")

# Aktualizacja tylko 1 pliku (watcher)
def update_from_change(path: Path):
    print(f"🔄 Aktualizacja z watchera: {path}")
    
    if not OUTPUT_FILE.exists():
        print("📄 knowledge.json nie istnieje, pełna synteza...")
        synthesise_all()
        return

    try:
        with OUTPUT_FILE.open(encoding="utf-8") as f:
            existing = json.load(f)
    except Exception as e:
        print(f"❌ Błąd przy odczycie knowledge.json: {e}", file=sys.stderr)
        synthesise_all()
        return

    files_data = existing.get("files", {})
    dependencies = existing.get("dependencies", {})
    symbols_index = existing.get("symbols", {})

    update_file_entry(path, files_data, dependencies, symbols_index)

    updated = {
        "files": files_data,
        "dependencies": dependencies,
        "symbols": symbols_index
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2)
        print(f"🔁 Zaktualizowano plik: {path.name}")

# Watchdog
class MetaEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory or not event.src_path.endswith(".json"):
            return
        print(f"📎 Wykryto zmianę: {event.src_path}")
        update_from_change(Path(event.src_path))

def watch_loop():
    observer = Observer()
    handler = MetaEventHandler()

    while True:
        if META_DIR.exists():
            observer.schedule(handler, str(META_DIR), recursive=True)
            print(f"👀 Obserwuję: {META_DIR}")
            observer.start()
            break
        else:
            print("⏳ Czekam na .meta...")
            time.sleep(2)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    watch_loop()