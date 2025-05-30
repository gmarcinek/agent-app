"""
Projekt Tree Widget z automatycznym odświeżaniem
"""
import os
from pathlib import Path
from textual.widgets import DirectoryTree
from textual.message import Message

class ProjectTree(DirectoryTree):
    """Drzewo projektu z automatycznym odświeżaniem"""
    DEFAULT_CSS = """
    ProjectTree {
        padding: 1 2;
    }
    """
    def __init__(self):
        # Ustaw domyślny katalog na 'output' jeśli istnieje, inaczej katalog główny
        root_path = Path("output") if Path("output").exists() else Path(".")
        super().__init__(root_path)
        
        # Timer do automatycznego odświeżania co 3 sekundy
        self.auto_refresh_enabled = True
        
        # Wymuś pokazanie root jako expandable
        self.show_root = True
    
    def on_mount(self):
        """Uruchom timer auto-refresh po zamontowaniu"""
        if self.auto_refresh_enabled:
            self.set_interval(3.0, self.auto_refresh)
    
    def auto_refresh(self):
        """Automatyczne odświeżanie zawartości drzewa"""
        try:
            # Sprawdź czy root path dalej istnieje
            if self.path.exists():
                # Użyj wbudowanej metody reload()
                self.reload()
            else:
                # Jeśli katalog nie istnieje, przełącz na katalog główny
                self.path = Path(".")
                self.reload()
        except Exception as e:
            # W przypadku błędu, zatrzymaj auto-refresh
            self.app.notify(f"⚠️ Auto-refresh error: {e}", severity="warning")
    
    def on_directory_tree_file_selected(self, event):
        """Obsługa wyboru pliku"""
        from gui.events import FileOpenRequest
        # Wyślij event do głównej aplikacji - używaj event.path zamiast tworzyć własny
        self.post_message(FileOpenRequest(event.path))
    
    def toggle_auto_refresh(self):
        """Przełącz auto-refresh on/off"""
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        if self.auto_refresh_enabled:
            self.set_interval(1.0, self.auto_refresh)
            self.app.notify("✅ Auto-refresh włączony")
        else:
            self.app.notify("⏹️ Auto-refresh wyłączony")
    
    def manual_refresh(self):
        """Ręczne odświeżenie"""
        try:
            self.reload()
            self.app.notify("🔄 Drzewo odświeżone")
        except Exception as e:
            self.app.notify(f"❌ Błąd odświeżania: {e}", severity="error")
    
    def set_root_path(self, path: str | Path):
        """Zmień katalog główny drzewa"""
        new_path = Path(path)
        if new_path.exists() and new_path.is_dir():
            self.path = new_path
            self.reload()
            self.app.notify(f"📁 Katalog zmieniony na: {path}")
        else:
            self.app.notify(f"❌ Katalog nie istnieje: {path}", severity="error")
    
    def render_label(self, node, base_style, style):
        """Custom render z wyraźnymi strzałkami"""
        if node._allow_expand:
            # Dodaj wyraźne strzałki
            arrow = "▼ " if node.is_expanded else "▶ "
            folder_icon = "📂" if node.is_expanded else "📁"
            label = f"{arrow}{folder_icon} {node._label}"
        else:
            # Plik
            label = f"📄 {node._label}"
        
        from rich.text import Text
        return Text(label)