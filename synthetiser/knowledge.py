import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from .config import get_config
from .processor import MetaFileProcessor


class KnowledgeBuilder:
    """Budowniczy i manager knowledge.json - głównej bazy wiedzy synthetiser'a"""
    
    def __init__(self):
        self.config = get_config()
        self.processor = MetaFileProcessor()
        self._last_build_time = 0
    
    def _get_meta_files(self) -> List[Path]:
        """Znajduje wszystkie pliki JSON w katalogu .meta/"""
        if not self.config.meta_dir.exists():
            if self.config.get("debug"):
                print(f"📂 Katalog .meta nie istnieje: {self.config.meta_dir}")
            return []
        
        json_files = list(self.config.meta_dir.rglob("*.json"))
        
        if self.config.get("debug"):
            print(f"🔍 Znaleziono {len(json_files)} plików JSON w .meta/:")
            for f in json_files[:10]:  # Pokaż max 10 dla czytelności
                print(f"  - {f.relative_to(self.config.meta_dir)}")
            if len(json_files) > 10:
                print(f"  ... i {len(json_files) - 10} więcej")
        
        return json_files
    
    def build_full_knowledge(self) -> Dict[str, Any]:
        """
        Buduje pełną bazę wiedzy od zera na podstawie wszystkich plików w .meta/
        
        Returns:
            dict: Kompletna struktura knowledge.json
        """
        start_time = time.time()
        
        if self.config.get("debug"):
            print("🧠 Budowanie pełnej bazy wiedzy...")
        
        # Znajdź wszystkie pliki meta
        meta_files = self._get_meta_files()
        
        if not meta_files:
            print("⚠️ Brak plików metadanych do przetworzenia")
            return self._empty_knowledge()
        
        # Przetwórz wszystkie pliki
        files_data, dependencies, symbols_index = self.processor.process_batch(meta_files)
        
        # Zbuduj strukturę knowledge
        knowledge = {
            "metadata": {
                "built_at": time.time(),
                "version": "1.0",
                "total_files": len(files_data),
                "total_symbols": len(symbols_index),
                "build_time_seconds": round(time.time() - start_time, 3)
            },
            "files": files_data,
            "dependencies": dependencies,
            "symbols": symbols_index
        }
        
        self._last_build_time = time.time()
        
        if self.config.get("debug"):
            self._debug_knowledge_stats(knowledge)
        
        return knowledge
    
    def update_incremental_knowledge(self, changed_file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Aktualizuje knowledge.json inkrementalnie dla pojedynczego zmienionego pliku
        
        Args:
            changed_file_path: Ścieżka do zmienionego pliku w .meta/
            
        Returns:
            dict: Zaktualizowana struktura knowledge.json lub None w przypadku błędu
        """
        if self.config.get("debug"):
            print(f"🔄 Aktualizacja inkrementalna dla: {changed_file_path.name}")
        
        # Wczytaj istniejące knowledge
        existing_knowledge = self.load_existing_knowledge()
        if existing_knowledge is None:
            if self.config.get("debug"):
                print("📄 Brak istniejącego knowledge.json, budowanie od zera...")
            return self.build_full_knowledge()
        
        # Przetwórz zmieniony plik
        file_result = self.processor.extract_file_metadata(changed_file_path)
        if file_result is None:
            if self.config.get("debug"):
                print(f"❌ Nie udało się przetworzyć {changed_file_path}")
            return existing_knowledge
        
        # Aktualizuj struktury
        files_data = existing_knowledge.get("files", {})
        dependencies = existing_knowledge.get("dependencies", {})
        symbols_index = existing_knowledge.get("symbols", {})
        
        file_path = file_result["path"]
        
        # Usuń stare eksporty tego pliku z indeksu symboli
        self._remove_file_symbols(symbols_index, file_path)
        
        # Dodaj nowe dane
        files_data[file_path] = file_result["metadata"]
        dependencies[file_path] = file_result["imports"]
        
        # Dodaj nowe eksporty
        for symbol in file_result["exports"]:
            if symbol in symbols_index and symbols_index[symbol]["file"] != file_path:
                existing_file = symbols_index[symbol]["file"]
                print(f"⚠️ Konflikt symbolu '{symbol}': zastępuję {existing_file} → {file_path}", file=sys.stderr)
            
            symbols_index[symbol] = {
                "file": file_path,
                "type": "export"
            }
        
        # Zaktualizuj metadata
        updated_knowledge = {
            "metadata": {
                "built_at": existing_knowledge.get("metadata", {}).get("built_at", time.time()),
                "version": "1.0",
                "last_updated": time.time(),
                "total_files": len(files_data),
                "total_symbols": len(symbols_index),
                "last_changed_file": file_path
            },
            "files": files_data,
            "dependencies": dependencies,
            "symbols": symbols_index
        }
        
        if self.config.get("debug"):
            print(f"✅ Zaktualizowano knowledge dla {file_path}")
        
        return updated_knowledge
    
    def save_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        """
        Zapisuje knowledge.json do pliku
        
        Args:
            knowledge: Struktura danych do zapisania
            
        Returns:
            bool: True jeśli zapis się powiódł
        """
        try:
            self.config.ensure_directories()
            
            with self.config.knowledge_file.open("w", encoding="utf-8") as f:
                json.dump(knowledge, f, indent=2, ensure_ascii=False)
            
            if self.config.get("debug"):
                print(f"💾 Zapisano knowledge.json: {self.config.knowledge_file}")
            else:
                print(f"🧠 Zaktualizowano: {self.config.knowledge_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd zapisu knowledge.json: {e}", file=sys.stderr)
            return False
    
    def load_existing_knowledge(self) -> Optional[Dict[str, Any]]:
        """
        Wczytuje istniejący plik knowledge.json
        
        Returns:
            dict: Istniejąca struktura knowledge lub None jeśli nie istnieje/błąd
        """
        if not self.config.knowledge_file.exists():
            return None
        
        try:
            with self.config.knowledge_file.open(encoding="utf-8") as f:
                knowledge = json.load(f)
                
            if self.config.get("debug"):
                print(f"📖 Wczytano istniejące knowledge.json")
                
            return knowledge
            
        except Exception as e:
            print(f"❌ Błąd wczytywania knowledge.json: {e}", file=sys.stderr)
            return None
    
    def rebuild_if_needed(self) -> Dict[str, Any]:
        """
        Przebudowuje knowledge jeśli jest to potrzebne (np. brak pliku, stary timestamp)
        
        Returns:
            dict: Aktualna struktura knowledge
        """
        existing = self.load_existing_knowledge()
        
        if existing is None:
            if self.config.get("debug"):
                print("🔄 Knowledge.json nie istnieje - budowanie od zera")
            return self.build_full_knowledge()
        
        # Sprawdź czy knowledge jest aktualny
        meta_files = self._get_meta_files()
        if not meta_files:
            return existing
        
        # Znajdź najnowszy plik meta
        newest_meta_time = max(f.stat().st_mtime for f in meta_files)
        knowledge_time = existing.get("metadata", {}).get("built_at", 0)
        
        if newest_meta_time > knowledge_time:
            if self.config.get("debug"):
                print("🔄 Znaleziono nowsze pliki meta - przebudowywanie knowledge")
            return self.build_full_knowledge()
        
        if self.config.get("debug"):
            print("✅ Knowledge.json jest aktualny")
        
        return existing
    
    def _empty_knowledge(self) -> Dict[str, Any]:
        """Zwraca pustą strukturę knowledge"""
        return {
            "metadata": {
                "built_at": time.time(),
                "version": "1.0",
                "total_files": 0,
                "total_symbols": 0
            },
            "files": {},
            "dependencies": {},
            "symbols": {}
        }
    
    def _remove_file_symbols(self, symbols_index: Dict[str, Dict[str, str]], file_path: str):
        """Usuwa wszystkie symbole należące do danego pliku z indeksu"""
        to_remove = [symbol for symbol, data in symbols_index.items() 
                    if data.get("file") == file_path]
        
        for symbol in to_remove:
            del symbols_index[symbol]
            
        if self.config.get("debug") and to_remove:
            print(f"🗑️ Usunięto {len(to_remove)} symboli dla {file_path}")
    
    def _debug_knowledge_stats(self, knowledge: Dict[str, Any]):
        """Wyświetla statystyki debug dla knowledge"""
        metadata = knowledge.get("metadata", {})
        files = knowledge.get("files", {})
        dependencies = knowledge.get("dependencies", {})
        symbols = knowledge.get("symbols", {})
        
        print("📊 Statystyki Knowledge:")
        print(f"  📄 Plików: {len(files)}")
        print(f"  🔗 Zależności: {len(dependencies)}")
        print(f"  🏷️ Symboli: {len(symbols)}")
        print(f"  ⏱️ Czas budowania: {metadata.get('build_time_seconds', 0)}s")
        
        # Top 5 plików z najwięcej eksportami
        file_exports = {}
        for symbol, data in symbols.items():
            file_path = data.get("file", "unknown")
            file_exports[file_path] = file_exports.get(file_path, 0) + 1
        
        if file_exports:
            top_exporters = sorted(file_exports.items(), key=lambda x: x[1], reverse=True)[:5]
            print("  📤 Top eksporterzy:")
            for file_path, count in top_exporters:
                print(f"    {Path(file_path).name}: {count} eksportów")
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Zwraca szczegółowe informacje o zależnościach dla danego pliku
        
        Args:
            file_path: Względna ścieżka pliku w .meta/
            
        Returns:
            dict: Informacje o zależnościach (imports, dependents, exports)
        """
        knowledge = self.load_existing_knowledge()
        if not knowledge:
            return {}
        
        dependencies = knowledge.get("dependencies", {})
        symbols = knowledge.get("symbols", {})
        
        # Importy tego pliku
        imports = dependencies.get(file_path, [])
        
        # Pliki które zależą od tego pliku
        dependents = [path for path, deps in dependencies.items() 
                     if any(imp in [s for s, data in symbols.items() 
                                  if data.get("file") == file_path] for imp in deps)]
        
        # Eksporty tego pliku
        exports = [symbol for symbol, data in symbols.items() 
                  if data.get("file") == file_path]
        
    def restore_from_backup(self) -> bool:
        """
        Przywraca knowledge.json z pliku backup
        
        Returns:
            bool: True jeśli restore się powiódł
        """
        backup_file = self.config.knowledge_file.with_suffix('.backup.json')
        
        if not backup_file.exists():
            print("❌ Brak pliku backup do przywrócenia")
            return False
        
        try:
            import shutil
            shutil.copy2(backup_file, self.config.knowledge_file)
            print(f"🔄 Przywrócono knowledge z backup: {backup_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd przywracania z backup: {e}")
            return False
    
    def compare_with_startup(self) -> Dict[str, Any]:
        """
        Porównuje obecny knowledge ze startup snapshot
        
        Returns:
            dict: Statystyki zmian od startu
        """
        startup_file = self.config.knowledge_file.with_suffix('.startup.json')
        
        if not startup_file.exists():
            return {"error": "Brak startup snapshot"}
        
        try:
            current = self.load_existing_knowledge()
            
            with startup_file.open(encoding="utf-8") as f:
                startup = json.load(f)
            
            if not current or not startup:
                return {"error": "Nie można wczytać plików"}
            
            current_files = len(current.get("files", {}))
            current_symbols = len(current.get("symbols", {}))
            startup_files = startup.get("startup_metadata", {}).get("startup_files_count", 0)
            startup_symbols = startup.get("startup_metadata", {}).get("startup_symbols_count", 0)
            
            return {
                "files_changed": current_files - startup_files,
                "symbols_changed": current_symbols - startup_symbols,
                "startup_time": startup.get("startup_metadata", {}).get("startup_time"),
                "runtime_seconds": time.time() - startup.get("startup_metadata", {}).get("startup_time", time.time())
            }
            
        except Exception as e:
            return {"error": f"Błąd porównania: {e}"}