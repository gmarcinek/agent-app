from analyser.scanner import is_text_file, should_ignore_file
from analyser.analyser import analyze_file
from constants.constants import IGNORED_DIRS
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import time
import asyncio
import os
import threading
from pathlib import Path

def should_ignore_path(filepath: str) -> bool:
    """Sprawdza czy ścieżka powinna być ignorowana"""
    path = Path(filepath)
    
    # Sprawdź czy jakakolwiek część ścieżki to ignorowany katalog
    if any(ignored_dir in path.parts for ignored_dir in IGNORED_DIRS):
        return True
    
    # Sprawdź czy nazwa pliku powinna być ignorowana
    if should_ignore_file(path.name):
        return True
        
    return False

class ChangeHandler(PatternMatchingEventHandler):
    def __init__(self):
        # Podstawowa konfiguracja - nie polegamy na ignore_patterns
        super().__init__(ignore_directories=True)
        self._pending = {}
        self._loop = None
        
    def set_loop(self, loop):
        self._loop = loop

    def on_modified(self, event):
        if event.is_directory:
            return

        path = os.path.normpath(event.src_path)
        
        # NOWE: Sprawdź czy ścieżka powinna być ignorowana
        if should_ignore_path(path):
            return
        
        # Sprawdź czy to plik tekstowy
        if not is_text_file(path):
            return

        now = time.time()
        
        print(f"🔄 Wykryto zmianę: {path}")

        # debounce: opóźnij analizę o 0.5s od ostatniej zmiany
        self._pending[path] = now

    async def watch_pending(self):
        """Obsługuje odłożone analizy"""
        while True:
            to_analyze = []
            now = time.time()
            for path, ts in list(self._pending.items()):
                if now - ts > 0.5:  # 500ms debounce
                    to_analyze.append(path)
                    del self._pending[path]
            
            for path in to_analyze:
                print(f"🔍 Analizuję: {path}")
                await analyze_file(path)
            
            await asyncio.sleep(0.25)

def start_analyser(watch_path="output/app"):
    """Uruchamia obserwator plików"""
    print(f"👀 Watcher uruchomiony dla {watch_path}/")
    
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, watch_path, recursive=True)
    observer.start()
    
    # Uruchom async loop w osobnym wątku
    def run_async_handler():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        handler.set_loop(loop)
        try:
            loop.run_until_complete(handler.watch_pending())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    
    async_thread = threading.Thread(target=run_async_handler, daemon=True)
    async_thread.start()
    
    try:
        observer.join()  # Czeka aż observer zostanie zatrzymany
    except KeyboardInterrupt:
        print("⏹️ Zatrzymywanie watchera...")
        observer.stop()
    observer.join()