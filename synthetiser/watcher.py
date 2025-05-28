import time
import threading
from pathlib import Path
from typing import Dict, Set, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from .config import get_config
from .knowledge import KnowledgeBuilder


class MetaFileWatcher:
    """
    Obserwator zmian w plikach metadanych z debouncing'iem i batch processing
    """
    
    def __init__(self, on_change_callback: Optional[Callable] = None):
        self.config = get_config()
        self.knowledge_builder = KnowledgeBuilder()
        self.on_change_callback = on_change_callback
        
        # Debouncing - grupowanie zmian w krótkim czasie
        self.pending_changes: Dict[str, float] = {}
        self.debounce_timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()
        
        # Observer watchdog
        self.observer: Optional[Observer] = None
        self.is_running = False
    
    def start_watching(self):
        """Rozpoczyna obserwację katalogu .meta/"""
        if self.is_running:
            print("⚠️ Watcher już działa")
            return
        
        # Sprawdź czy katalog .meta istnieje
        if not self._wait_for_meta_dir():
            print("❌ Nie udało się znaleźć katalogu .meta/")
            return
        
        # Zbuduj initial knowledge
        self._build_initial_knowledge()
        
        # Uruchom obserwację
        self.observer = Observer()
        handler = MetaEventHandler(self)
        self.observer.schedule(handler, str(self.config.meta_dir), recursive=True)
        
        try:
            self.observer.start()
            self.is_running = True
            print(f"👀 Obserwuję zmiany w: {self.config.meta_dir}")
            
            if self.config.get("debug"):
                print(f"🔧 Debounce delay: {self.config.get('debounce_delay')}s")
            
        except Exception as e:
            print(f"❌ Błąd uruchamiania watchera: {e}")
            self.is_running = False
    
    def stop_watching(self):
        """Zatrzymuje obserwację"""
        if not self.is_running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        # Anuluj pending timer
        with self.lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
                self.debounce_timer = None
        
        self.is_running = False
        print("🛑 Zatrzymano obserwację")
    
    def wait_for_completion(self):
        """Blokuje do momentu przerwania (Ctrl+C)"""
        if not self.is_running:
            print("❌ Watcher nie jest uruchomiony")
            return
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Przerwano przez użytkownika")
        finally:
            self.stop_watching()
    
    def handle_file_change(self, file_path: Path, event_type: str):
        """
        Obsługuje zmianę pliku z debouncing'iem
        
        Args:
            file_path: Ścieżka do zmienionego pliku
            event_type: Typ zdarzenia (created, modified, deleted)
        """
        if not self._is_relevant_file(file_path):
            return
        
        current_time = time.time()
        file_key = str(file_path)
        
        with self.lock:
            # Zapisz zmianę z timestamp
            self.pending_changes[file_key] = current_time
            
            if self.config.get("debug"):
                print(f"📎 Wykryto zmianę ({event_type}): {file_path.name}")
            
            # Anuluj poprzedni timer i ustaw nowy
            if self.debounce_timer:
                self.debounce_timer.cancel()
            
            delay = self.config.get("debounce_delay", 0.5)
            self.debounce_timer = threading.Timer(delay, self._process_pending_changes)
            self.debounce_timer.start()
    
    def _process_pending_changes(self):
        """Przetwarza wszystkie pending zmiany po debounce delay"""
        with self.lock:
            if not self.pending_changes:
                return
            
            changes_to_process = self.pending_changes.copy()
            self.pending_changes.clear()
            self.debounce_timer = None
        
        if self.config.get("debug"):
            print(f"🔄 Przetwarzam {len(changes_to_process)} zmian po debounce")
        
        # Grupuj zmiany według czasu - jeśli dużo zmian naraz, rób full rebuild
        recent_changes = [path for path, timestamp in changes_to_process.items() 
                         if time.time() - timestamp < 2.0]
        
        batch_threshold = self.config.get("batch_size", 10)
        
        if len(recent_changes) >= batch_threshold:
            if self.config.get("debug"):
                print(f"🏗️ Dużo zmian ({len(recent_changes)}), full rebuild")
            self._do_full_rebuild()
        else:
            if self.config.get("debug"):
                print(f"🔧 Mało zmian ({len(recent_changes)}), incremental updates")
            self._do_incremental_updates(recent_changes)
        
        # Wywołaj callback jeśli jest ustawiony
        if self.on_change_callback:
            try:
                self.on_change_callback(recent_changes)
            except Exception as e:
                print(f"❌ Błąd w callback: {e}")
    
    def _do_full_rebuild(self):
        """Wykonuje pełną przebudowę knowledge"""
        try:
            knowledge = self.knowledge_builder.build_full_knowledge()
            success = self.knowledge_builder.save_knowledge(knowledge)
            
            if success:
                print("🧠 Pełna przebudowa knowledge zakończona")
            else:
                print("❌ Błąd podczas pełnej przebudowy")
                
        except Exception as e:
            print(f"❌ Błąd pełnej przebudowy: {e}")
    
    def _do_incremental_updates(self, changed_files: list):
        """Wykonuje incremental updates dla listy plików"""
        success_count = 0
        
        for file_path_str in changed_files:
            try:
                file_path = Path(file_path_str)
                
                if not file_path.exists():
                    if self.config.get("debug"):
                        print(f"🗑️ Plik usunięty: {file_path.name}")
                    # TODO: Obsługa usuwania plików z knowledge
                    continue
                
                knowledge = self.knowledge_builder.update_incremental_knowledge(file_path)
                
                if knowledge:
                    success = self.knowledge_builder.save_knowledge(knowledge)
                    if success:
                        success_count += 1
                        if not self.config.get("debug"):
                            print(f"🔁 Zaktualizowano: {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Błąd aktualizacji {file_path_str}: {e}")
        
        if self.config.get("debug"):
            print(f"✅ Zaktualizowano {success_count}/{len(changed_files)} plików")
    
    def _wait_for_meta_dir(self, timeout: int = 30) -> bool:
        """
        Czeka na pojawienie się katalogu .meta/ 
        
        Args:
            timeout: Maksymalny czas oczekiwania w sekundach
            
        Returns:
            bool: True jeśli katalog został znaleziony
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.config.meta_dir.exists():
                if self.config.get("debug"):
                    print(f"✅ Znaleziono katalog .meta/")
                return True
            
            print(f"⏳ Czekam na katalog .meta/... ({int(time.time() - start_time)}s)")
            time.sleep(2)
        
        return False
    
    def _build_initial_knowledge(self):
        """Buduje początkową wersję knowledge przy starcie"""
        try:
            if self.config.get("debug"):
                print("🏗️ Budowanie początkowego knowledge...")
            
            # Backup istniejącego knowledge (jeśli istnieje)
            self._create_backup()
            
            knowledge = self.knowledge_builder.rebuild_if_needed()
            self.knowledge_builder.save_knowledge(knowledge)
            
            # Zapisz snapshot przy starcie
            self._create_startup_snapshot(knowledge)
            
            if self.config.get("debug"):
                print("✅ Początkowe knowledge gotowe")
                
        except Exception as e:
            print(f"❌ Błąd budowania początkowego knowledge: {e}")
    
    def _create_backup(self):
        """Tworzy backup istniejącego knowledge.json"""
        if not self.config.knowledge_file.exists():
            return
            
        try:
            backup_file = self.config.knowledge_file.with_suffix('.backup.json')
            
            # Skopiuj obecny knowledge do backup
            import shutil
            shutil.copy2(self.config.knowledge_file, backup_file)
            
            if self.config.get("debug"):
                print(f"💾 Utworzono backup: {backup_file.name}")
            else:
                print(f"💾 Backup knowledge: {backup_file.name}")
                
        except Exception as e:
            print(f"⚠️ Błąd tworzenia backup: {e}")
    
    def _create_startup_snapshot(self, knowledge: dict):
        """Tworzy snapshot knowledge przy starcie"""
        try:
            startup_file = self.config.knowledge_file.with_suffix('.startup.json')
            
            # Dodaj metadata o starcie
            snapshot = knowledge.copy()
            snapshot["startup_metadata"] = {
                "startup_time": time.time(),
                "startup_version": knowledge.get("metadata", {}).get("version", "unknown"),
                "startup_files_count": len(knowledge.get("files", {})),
                "startup_symbols_count": len(knowledge.get("symbols", {}))
            }
            
            with startup_file.open("w", encoding="utf-8") as f:
                import json
                json.dump(snapshot, f, indent=2)
            
            if self.config.get("debug"):
                print(f"📸 Utworzono startup snapshot: {startup_file.name}")
                
        except Exception as e:
            print(f"⚠️ Błąd tworzenia startup snapshot: {e}")
    
    def _is_relevant_file(self, file_path: Path) -> bool:
        """
        Sprawdza czy plik jest relevantny dla obserwacji
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            bool: True jeśli plik powinien być obserwowany
        """
        # Tylko pliki JSON
        if file_path.suffix.lower() != ".json":
            return False
        
        # Musi być w katalogu .meta
        try:
            file_path.relative_to(self.config.meta_dir)
        except ValueError:
            return False
        
        # Ignoruj pliki tymczasowe
        if file_path.name.startswith('.') or file_path.name.endswith('.tmp'):
            return False
        
        # Ignoruj node_modules
        if "node_modules" in str(file_path):
            return False
        
        return True
    
    def get_status(self) -> Dict[str, any]:
        """Zwraca status watchera"""
        return {
            "is_running": self.is_running,
            "watching_directory": str(self.config.meta_dir),
            "pending_changes": len(self.pending_changes),
            "has_timer": self.debounce_timer is not None,
            "config": {
                "debounce_delay": self.config.get("debounce_delay"),
                "batch_size": self.config.get("batch_size"),
                "debug": self.config.get("debug")
            }
        }


class MetaEventHandler(FileSystemEventHandler):
    """Handler dla zdarzeń systemu plików - bridge między watchdog a MetaFileWatcher"""
    
    def __init__(self, watcher: MetaFileWatcher):
        self.watcher = watcher
        super().__init__()
    
    def on_any_event(self, event: FileSystemEvent):
        """Obsługuje wszystkie zdarzenia systemu plików"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        event_type = event.event_type
        
        self.watcher.handle_file_change(file_path, event_type)
    
    def on_moved(self, event):
        """Obsługuje przeniesienie pliku"""
        if event.is_directory:
            return
        
        # Traktuj jako usunięcie starego i dodanie nowego
        old_path = Path(event.src_path)
        new_path = Path(event.dest_path)
        
        self.watcher.handle_file_change(old_path, "deleted")
        self.watcher.handle_file_change(new_path, "created")


def start_meta_watcher(callback: Optional[Callable] = None) -> MetaFileWatcher:
    """
    Convenience function do uruchamiania watchera
    
    Args:
        callback: Opcjonalny callback wywoływany po każdej zmianie
        
    Returns:
        MetaFileWatcher: Uruchomiony watcher
    """
    watcher = MetaFileWatcher(callback)
    watcher.start_watching()
    return watcher