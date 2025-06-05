import os
import shutil
from logger import get_log_hub
from constants.constants import IGNORED_DIRS

class FileSystem:
    def __init__(self, base_path: str = "output"):
        self.base_path = os.path.abspath(base_path)
        self.log_hub = get_log_hub()
        os.makedirs(self.base_path, exist_ok=True)
        self.cwd = self.base_path

    def cd(self, relative_path: str):
        new_path = os.path.abspath(os.path.join(self.cwd, relative_path))
        if not new_path.startswith(self.base_path):
            self.log_hub.error("FILESYSTEM", f"Próba wyjścia poza katalog roboczy: {relative_path}")
            raise ValueError("Próba wyjścia poza katalog roboczy")
        if not os.path.isdir(new_path):
            self.log_hub.error("FILESYSTEM", f"Nie istnieje katalog: {relative_path}")
            raise FileNotFoundError(f"Nie istnieje katalog: {relative_path}")
        self.cwd = new_path

    def ls(self) -> list[str]:
        return os.listdir(self.cwd)

    def read_file(self, filename: str) -> str:
        path = os.path.join(self.cwd, filename)
        if not os.path.isfile(path):
            self.log_hub.error("FILESYSTEM", f"Plik nie istnieje: {filename}")
            raise FileNotFoundError(f"Plik nie istnieje: {filename}")
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd odczytu pliku {filename}: {e}")
            raise

    def write_file(self, filename: str, content: str):
        path = os.path.join(self.cwd, filename)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd zapisu pliku {filename}: {e}")
            raise

    def mkdir(self, dir_name: str):
        path = os.path.join(self.cwd, dir_name)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd tworzenia katalogu {dir_name}: {e}")
            raise

    def rm(self, target: str):
        path = os.path.join(self.cwd, target)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                self.log_hub.error("FILESYSTEM", f"Błąd usuwania pliku {target}: {e}")
                raise
        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                self.log_hub.error("FILESYSTEM", f"Błąd usuwania katalogu {target}: {e}")
                raise
        else:
            self.log_hub.error("FILESYSTEM", f"Nie znaleziono: {target}")
            raise FileNotFoundError(f"Nie znaleziono: {target}")

    def pwd(self) -> str:
        return os.path.relpath(self.cwd, self.base_path)

    def get_flat_file_list(self) -> list[str]:
        all_files = []
        try:
            for dirpath, dirnames, filenames in os.walk(self.base_path):
                dirnames[:] = [d for d in dirnames if d != "node_modules"]
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    all_files.append(os.path.normpath(full_path))
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd skanowania katalogów: {e}")
            raise
        return all_files
    
    def is_ignored_path(self, file_path: str) -> bool:
        """Sprawdza czy ścieżka zawiera ignorowane katalogi"""
        path_parts = file_path.split(os.sep)
        return any(ignored_dir in path_parts for ignored_dir in IGNORED_DIRS)

    def get_flat_file_list_string(self) -> str:
        """Zwraca tylko pliki z katalogu projektu (output/app)"""
        try:
            app_path = os.path.join(self.base_path, "app") 
            if not os.path.exists(app_path):
                return "(Projekt nie istnieje)"
                
            # Skanuj tylko output/app
            temp_fs = FileSystem(app_path)
            files = temp_fs.get_flat_file_list()
            
            # Konwertuj bezwzględne ścieżki na relatywne względem app_path
            relative_files = []
            for f in files:
                if f.startswith(app_path):
                    rel_path = os.path.relpath(f, app_path)
                    relative_files.append(rel_path)
            
            # Dodaj prefix i filtruj
            project_files = [f"output/app/{f.replace(os.sep, '/')}" for f in relative_files]
            filtered = [f for f in project_files if not self.is_ignored_path(f)]
            
            return "\n".join(filtered) if filtered else "(Brak plików w projekcie)"
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd generowania listy plików projektu: {e}")
            raise

# Funkcja pomocnicza do użycia bezpośrednio
def get_flat_file_list_string(base_path: str = "output") -> str:
    fs = FileSystem(base_path)
    return fs.get_flat_file_list_string()