import os
import shutil
from logger import get_log_hub

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

    def get_flat_file_list_string(self) -> str:
        try:
            files = self.get_flat_file_list()
            filtered = [f for f in files if os.sep + "node_modules" + os.sep not in f and os.sep + "logs" + os.sep not in f]
            if not filtered:
                return f"(Brak plików w katalogu '{self.base_path}')"
            return "\n".join(filtered)
        except Exception as e:
            self.log_hub.error("FILESYSTEM", f"Błąd generowania listy plików: {e}")
            raise

# Funkcja pomocnicza do użycia bezpośrednio
def get_flat_file_list_string(base_path: str = "output") -> str:
    fs = FileSystem(base_path)
    return fs.get_flat_file_list_string()