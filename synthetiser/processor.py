import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from constants.constants import LANGUAGE_MAP, TEXT_EXTENSIONS, COMMON_TEXT_FILES
from .config import get_config


class MetaFileProcessor:
    """Procesor do przetwarzania pojedynczych plików metadanych"""
    
    def __init__(self):
        self.config = get_config()
    
    def is_valid_meta_file(self, path: Path) -> bool:
        """
        Sprawdza czy plik jest poprawnym plikiem metadanych do przetworzenia
        """
        if self.config.get("debug"):
            print(f"🔍 Sprawdzam: {path}")
        
        # Podstawowe sprawdzenia
        if not path.is_file():
            if self.config.get("debug"):
                print(f"  ❌ Nie jest plikiem")
            return False
        
        if path.suffix.lower() != ".json":
            if self.config.get("debug"):
                print(f"  ❌ Nie jest plikiem JSON (suffix: {path.suffix})")
            return False
        
        # Nie przetwarzamy plików z node_modules (bezpieczeństwo)
        if "node_modules" in str(path):
            if self.config.get("debug"):
                print(f"  ❌ Plik z node_modules")
            return False
        
        # Synthetiser obserwuje tylko .meta/ więc wszystko inne jest OK
        if self.config.get("debug"):
            print(f"  ✅ Plik poprawny")
        
        return True
    
    def safe_load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Bezpiecznie wczytuje plik JSON z obsługą błędów
        """
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
                
            if self.config.get("debug"):
                print(f"✅ Wczytano JSON z {path.name}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Błąd JSON w {path}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"❌ Błąd wczytywania {path}: {e}", file=sys.stderr)
            return None
    
    def assign_weight(self, file_path: str) -> float:
        """
        Przypisuje wagę plikowi na podstawie jego nazwy i typu
        """
        path_obj = Path(file_path)
        
        # Pliki index.* mają mniejszą wagę, ALE z wyjątkami
        if "index." in path_obj.name:
            # Sprawdź oryginalny plik (bez .analysis.json) żeby wykryć CSS
            original_name = path_obj.name.replace('.analysis.json', '')
            original_path = Path(original_name)
            
            # Wyjątki: główne pliki stylów mają normalną wagę
            if original_path.suffix.lower() in ['.css', '.scss', '.sass', '.less']:
                weight = 1.0
                if self.config.get("debug"):
                    print(f"📊 Waga dla {path_obj.name}: {weight} (main stylesheet)")
                return weight
            
            # Inne pliki index.* (index.js, index.ts, index.html) - mniejsza waga
            weight = self.config.get("index_weight", 0.2)
            if self.config.get("debug"):
                print(f"📊 Waga dla {path_obj.name}: {weight} (index file)")
            return weight
        
        # Standardowa waga
        weight = 1.0
        if self.config.get("debug"):
            print(f"📊 Waga dla {path_obj.name}: {weight} (standard)")
        return weight
    
    def infer_language(self, file_path: str) -> Tuple[Optional[str], str, bool]:
        """
        Wykrywa język programowania na podstawie rozszerzenia pliku
        
        Returns:
            tuple: (language_name, extension, is_text_file)
        """
        path_obj = Path(file_path)
        suffix = path_obj.suffix.lower()
        name = path_obj.stem
        
        # Mapowanie rozszerzenia na język
        language = LANGUAGE_MAP.get(suffix)
        
        # Sprawdzenie czy to plik tekstowy
        is_text = suffix in TEXT_EXTENSIONS or name in COMMON_TEXT_FILES
        
        if self.config.get("debug"):
            print(f"🔤 Język dla {file_path}: {language}, rozszerzenie: {suffix}, tekst: {is_text}")
        
        return language, suffix, is_text
    
    def extract_file_metadata(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Wyciąga metadane z pojedynczego pliku analizy
        
        Returns:
            dict: Przetworzone metadane lub None w przypadku błędu
        """
        if not self.is_valid_meta_file(path):
            return None
        
        # Wczytaj dane JSON
        raw_data = self.safe_load_json(path)
        if raw_data is None:
            return None
        
        # Względna ścieżka do pliku w .meta/
        try:
            rel_path = str(path.relative_to(self.config.meta_dir))
        except ValueError:
            print(f"❌ Plik {path} nie jest w katalogu .meta/", file=sys.stderr)
            return None
        
        if self.config.get("debug"):
            print(f"📁 Przetwarzam: {rel_path}")
        
        # Wykryj język i typ
        language, extension, is_text = self.infer_language(rel_path)
        
        # Przypisz wagę
        weight = self.assign_weight(rel_path)
        
        # Przygotuj strukturę metadanych
        metadata = {
            "meta": raw_data,
            "weight": weight,
            "language": language,
            "extension": extension,
            "text": is_text,
            "processed_at": path.stat().st_mtime,  # timestamp ostatniej modyfikacji
        }
        
        if self.config.get("debug"):
            print(f"✅ Przetworzone metadane dla {rel_path}")
        
        return {
            "path": rel_path,
            "metadata": metadata,
            "imports": raw_data.get("imports", []),
            "exports": raw_data.get("exports", [])
        }
    
    def extract_dependencies(self, processed_files: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Wyciąga mapę zależności z przetworzonych plików
        """
        dependencies = {}
        
        for file_data in processed_files:
            path = file_data["path"]
            imports = file_data.get("imports", [])
            dependencies[path] = imports
            
            if self.config.get("debug") and imports:
                print(f"📦 Zależności {path}: {imports}")
        
        return dependencies
    
    def extract_symbols_index(self, processed_files: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """
        Buduje indeks symboli (eksportów) z przetworzonych plików
        """
        symbols_index = {}
        
        for file_data in processed_files:
            path = file_data["path"]
            exports = file_data.get("exports", [])
            
            for symbol in exports:
                if symbol in symbols_index:
                    # Konflikt nazw - loguj ostrzeżenie
                    existing_file = symbols_index[symbol]["file"]
                    print(f"⚠️ Konflikt symbolu '{symbol}': {existing_file} vs {path}", file=sys.stderr)
                
                symbols_index[symbol] = {
                    "file": path,
                    "type": "export"
                }
            
            if self.config.get("debug") and exports:
                print(f"📤 Eksporty {path}: {exports}")
        
        return symbols_index
    
    def process_batch(self, file_paths: List[Path]) -> Tuple[Dict[str, Any], Dict[str, List[str]], Dict[str, Dict[str, str]]]:
        """
        Przetwarza listę plików i zwraca kompletne struktury danych
        
        Returns:
            tuple: (files_data, dependencies, symbols_index)
        """
        processed_files = []
        files_data = {}
        
        if self.config.get("debug"):
            print(f"🔄 Przetwarzam batch {len(file_paths)} plików")
        
        # Przetwórz każdy plik
        for file_path in file_paths:
            result = self.extract_file_metadata(file_path)
            if result:
                processed_files.append(result)
                files_data[result["path"]] = result["metadata"]
        
        # Wyciągnij zależności i symbole
        dependencies = self.extract_dependencies(processed_files)
        symbols_index = self.extract_symbols_index(processed_files)
        
        if self.config.get("debug"):
            print(f"📊 Wyniki batch: {len(files_data)} plików, {len(symbols_index)} symboli")
        
        return files_data, dependencies, symbols_index