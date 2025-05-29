from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static
from gui.widgets.project_tree import ProjectTree
from gui.widgets.tab_manager import TabManager  # Zmiana: TabManager zamiast FileContentView
from gui.events import FileOpenRequest  # Dodaj import eventu

class TitleStatusBar(Static):
    """Placeholder dla title bar"""
    def compose(self) -> ComposeResult:
        yield Static("TitleStatusBar Widget", id="title-placeholder")

class FolderContentView(Static):
    """Placeholder dla folder content"""
    def compose(self) -> ComposeResult:
        yield Static("FolderContentView Widget", id="folder-placeholder")

class LogsSection(Static):
    """Placeholder dla logs"""
    def compose(self) -> ComposeResult:
        yield Static("LogsSection Widget", id="logs-placeholder")

class MainPromptSection(Static):
    """Placeholder dla main prompt"""
    def compose(self) -> ComposeResult:
        yield Static("MainPromptSection Widget", id="prompt-placeholder")

class AgentDashboard(App):
    """Minimalna aplikacja - tylko struktura"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #editor-section {
        height: 3fr;
        min-height: 10;
        margin: 0;
    }
    
    #tree-panel {
        width: 25%;
        min-width: 10;
        margin: 0 1 0 0;
        padding: 0;
        background: $surface;
    }
    
    #content-panel {
        width: 75%;
        min-width: 20;
        padding: 1;
        background: $surface;
    }
    
    LogsSection {
        margin: 0;
    }

    #log-panel {
        height: 3;
        min-height: 1;
        background: $surface;
        padding: 1;
        margin: 1 0 0 0;
    }
    
    MainPromptSection {
        margin: 0;
    }

    #prompt-panel {
        height: 2fr;
        min-height: 20%;
        padding: 1;
        background: $surface;
        margin: 1 0 0 0;
    }
    
    Static {
        margin: 0;
        padding: 0;
    }

    * {
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 1;
    }
    
    Scrollbar {
        background: $surface;
    }
    
    ScrollbarTrack {
        background: $surface;
    }
    
    ScrollbarThumb {
        background: $primary;
    }
    
    ScrollbarThumb:hover {
        background: $accent;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Komponowanie struktury aplikacji"""
        with Vertical():
            # Sekcja editora - podzielona poziomo na drzewo i podgląd
            with Horizontal(id="editor-section"):
                # Panel drzewa plików z przewijaniem
                with VerticalScroll(id="tree-panel"):
                    yield ProjectTree()
                
                # TabManager zamiast FileContentView
                with VerticalScroll(id="content-panel"):
                    yield TabManager()  # ZMIANA: TabManager zamiast FileContentView
            
            # Sekcja logów z przewijaniem
            with VerticalScroll(id="log-panel"):
                yield LogsSection()
            
            # Sekcja głównego promptu z przewijaniem
            with VerticalScroll(id="prompt-panel"):
                yield MainPromptSection()

    def on_file_open_request(self, event: FileOpenRequest) -> None:
        """Obsługuje żądanie otwarcia pliku"""
        tab_manager = self.query_one(TabManager)
        tab_manager.open_file(event.file_path)

    def on_mount(self) -> None:
        """Inicjalizacja po uruchomieniu"""
        self.theme = "gruvbox"
        # Usuń linijkę z file_viewer.show_placeholder() - nie potrzebna

def main():
    """Entry point"""
    app = AgentDashboard()
    app.run()

if __name__ == "__main__":
    main()