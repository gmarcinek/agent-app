from pathlib import Path
from textual.widgets import Tree
from gui.events import FileOpenRequest  # Dodaj ten import

class ProjectTree(Tree):
    """Proste drzewo plików ze stylizacją"""
    
    # Minimalne CSS - tylko padding
    DEFAULT_CSS = """
    ProjectTree {
        padding: 1 2;
    }
    """
    
    def __init__(self):
        self.root_path = self._find_output_folder()
        super().__init__(f"{self.root_path.name}/")
        self.show_root = True
        self.show_guides = True
        
        # Mapa ścieżek do węzłów
        self.path_to_node = {}
        
    def _find_output_folder(self) -> Path:
        """Znajdź folder output"""
        current_dir = Path.cwd()
        
        possible_paths = [
            current_dir / "output",
            current_dir.parent / "output",
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path.resolve()
        
        return current_dir
    
    def on_mount(self) -> None:
        """Zbuduj drzewo"""
        self._build_tree(self.root, self.root_path)
        self.root.expand()  
        
        # Otwórz też katalog app jeśli istnieje
        app_path = self.root_path / "app"
        if str(app_path) in self.path_to_node:
            self.path_to_node[str(app_path)].expand()
        
    def _build_tree(self, parent_node, dir_path: Path):
        """Zbuduj zawartość katalogu"""
        self.path_to_node[str(dir_path)] = parent_node
        
        try:
            items = list(dir_path.iterdir())
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if self._should_skip(item):
                    continue
                    
                if item.is_dir():
                    # Katalog - dodaj węzeł
                    dir_node = parent_node.add(item.name)
                    self.path_to_node[str(item)] = dir_node
                    # Zbuduj zawartość (ale węzeł będzie zamknięty)
                    self._build_tree(dir_node, item)
                else:
                    # Plik - dodaj liść
                    file_node = parent_node.add_leaf(item.name)
                    self.path_to_node[str(item)] = file_node
                    
        except (PermissionError, OSError):
            parent_node.add_leaf("Access denied")
    
    def _should_skip(self, path: Path) -> bool:
        """Sprawdź czy pominąć"""
        skip_names = {
            '__pycache__', '.git', '.vscode', 'node_modules', 'context', 'scenario.json',
            'state.json', 'logs', '.pytest_cache', '.mypy_cache', 'venv', '.venv'
        }
        
        return path.name in skip_names
    
    def on_tree_node_selected(self, event) -> None:
        """Obsłuż kliknięcie - wyślij event zamiast bezpośredniego wywołania"""
        node = event.node
        if not node:
            return
        
        # Znajdź ścieżkę
        file_path = None
        for path_str, mapped_node in self.path_to_node.items():
            if mapped_node == node:
                file_path = Path(path_str)
                break
        
        # Wyślij event jeśli to plik
        if file_path and file_path.is_file():
            self.post_message(FileOpenRequest(file_path))