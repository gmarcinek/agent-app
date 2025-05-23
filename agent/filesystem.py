import os
import shutil

class FileSystem:
    def __init__(self, base_path: str = "output"):
        self.base_path = os.path.abspath(base_path)
        os.makedirs(self.base_path, exist_ok=True)
        self.cwd = self.base_path

    def cd(self, relative_path: str):
        new_path = os.path.abspath(os.path.join(self.cwd, relative_path))
        if not new_path.startswith(self.base_path):
            raise ValueError("Próba wyjścia poza katalog roboczy")
        if not os.path.isdir(new_path):
            raise FileNotFoundError(f"Nie istnieje katalog: {relative_path}")
        self.cwd = new_path

    def ls(self) -> list[str]:
        return os.listdir(self.cwd)

    def read_file(self, filename: str) -> str:
        path = os.path.join(self.cwd, filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Plik nie istnieje: {filename}")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def write_file(self, filename: str, content: str):
        path = os.path.join(self.cwd, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def mkdir(self, dir_name: str):
        path = os.path.join(self.cwd, dir_name)
        os.makedirs(path, exist_ok=True)

    def rm(self, target: str):
        path = os.path.join(self.cwd, target)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            raise FileNotFoundError(f"Nie znaleziono: {target}")

    def pwd(self) -> str:
        return os.path.relpath(self.cwd, self.base_path)

    def get_flat_file_list(self) -> list[str]:
        all_files = []
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            dirnames[:] = [d for d in dirnames if d != "node_modules"]
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                all_files.append(os.path.normpath(full_path))
        return all_files

    def get_flat_file_list_string(self) -> str:
        files = self.get_flat_file_list()
        filtered = [f for f in files if os.sep + "node_modules" + os.sep not in f and os.sep + "logs" + os.sep not in f]
        if not filtered:
            return f"(Brak plików w katalogu '{self.base_path}')"
        return "\n".join(filtered)

# Funkcja pomocnicza do użycia bezpośrednio
def get_flat_file_list_string(base_path: str = "output") -> str:
    fs = FileSystem(base_path)
    return fs.get_flat_file_list_string()
