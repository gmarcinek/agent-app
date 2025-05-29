from pathlib import Path
from textual.widgets import Tree
from textual.app import ComposeResult


class ProjectTree(Tree):
    """Proste drzewo plików - pokazuje zawartość output/"""
    
    def __init__(self):
        # Znajdź folder output
        self.root_path = self._find_output_folder()
        
        super().__init__(f"📁 {self.root_path.name}/")
        self.show_root = True
        self.show_guides = True
        
        # Mapa ścieżek do węzłów dla łatwego wyszukiwania
        self.path_to_node = {}
        
    def _find_output_folder(self) -> Path:
        """Znajdź folder output w projekcie"""
        current_dir = Path.cwd()
        
        # Różne możliwe lokalizacje
        possible_paths = [
            current_dir / "output",           # Bezpośrednio w CWD
            current_dir.parent / "output",    # Poziom wyżej
            Path(__file__).parent.parent / "output",  # Względem gui/
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return path.resolve()
        
        # Fallback - użyj CWD
        return current_dir
    
    def on_mount(self) -> None:
        """Zbuduj drzewo gdy widget się ładuje"""
        self._build_tree()
        self.root.expand()
        
    def _build_tree(self):
        """Zbuduj zawartość drzewa"""
        # Wyczyść
        self.root.remove_children()
        self.path_to_node = {str(self.root_path): self.root}
        
        if not self.root_path.exists():
            self.root.add_leaf("❌ Output folder not found")
            return
        
        try:
            # Pobierz wszystkie elementy
            items = list(self.root_path.iterdir())
            
            # Sortuj: katalogi pierwsze, potem pliki, alfabetycznie
            items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
            
            # Dodaj do drzewa
            for item in items:
                if self._should_skip(item):
                    continue
                self._add_item(self.root, item)
                
        except Exception as e:
            self.root.add_leaf(f"❌ Error: {str(e)}")
    
    def _should_skip(self, path: Path) -> bool:
        """Sprawdź czy pominąć plik/katalog"""
        skip_names = {
            '__pycache__', '.git', '.vscode', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'venv', '.venv'
        }
        
        return path.name in skip_names or path.name.startswith('.')
    
    def _add_item(self, parent_node, item_path: Path):
        """Dodaj element do drzewa"""
        icon = self._get_icon(item_path)
        label = f"{icon} {item_path.name}"
        
        if item_path.is_dir():
            # Katalog - dodaj jako węzeł z dziećmi
            dir_node = parent_node.add(label)
            self.path_to_node[str(item_path)] = dir_node
            
            # Dodaj zawartość katalogu (jeden poziom)
            try:
                children = [child for child in item_path.iterdir() if not self._should_skip(child)]
                children.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
                
                for child in children[:20]:  # Limit 20 elementów na katalog
                    child_icon = self._get_icon(child)
                    child_label = f"{child_icon} {child.name}"
                    
                    if child.is_dir():
                        child_node = dir_node.add(child_label)
                        self.path_to_node[str(child)] = child_node
                        # Nie rozwijamy głębiej - lazy loading później
                    else:
                        file_node = dir_node.add_leaf(child_label)
                        self.path_to_node[str(child)] = file_node
                        
            except (PermissionError, OSError):
                dir_node.add_leaf("❌ Access denied")
        else:
            # Plik - dodaj jako liść
            file_node = parent_node.add_leaf(label)
            self.path_to_node[str(item_path)] = file_node
    
    def _get_icon(self, path: Path) -> str:
        """Pobierz ikonę dla pliku/katalogu"""
        if path.is_dir():
            return "📁"
        
        # Ikony według rozszerzenia
        suffix = path.suffix.lower()
        icons = {
            '.py': '🐍',
            '.js': '📘', '.ts': '📘', '.jsx': '⚛️', '.tsx': '⚛️',
            '.html': '🌐', '.css': '🎨',
            '.json': '📋', '.yaml': '⚙️', '.yml': '⚙️',
            '.md': '📝', '.txt': '📄',
            '.png': '🖼️', '.jpg': '🖼️', '.gif': '🖼️',
            '.zip': '📦', '.tar': '📦', '.gz': '📦',
        }
        
        return icons.get(suffix, '📄')
    
    def on_tree_node_selected(self, event) -> None:
        """Obsłuż kliknięcie w węzeł"""
        node = event.node
        if not node:
            return
        
        # Znajdź ścieżkę dla tego węzła
        file_path = None
        for path_str, mapped_node in self.path_to_node.items():
            if mapped_node == node:
                file_path = Path(path_str)
                break
        
        if not file_path:
            return
        
        # Pokaż toast z informacją
        if file_path.is_dir():
            self.notify(f"📁 Selected folder: {file_path.name}", severity="info")
        else:
            self.notify(f"📄 Selected file: {file_path.name}", severity="info")
        
        # TODO: Tutaj będzie komunikacja z główną aplikacją
        # self.app.handle_file_selection(file_path)