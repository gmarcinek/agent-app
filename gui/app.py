"""
Główna aplikacja GUI z integracją Process Manager
"""
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static
import atexit

# Import istniejących widgetów
from gui.widgets.project_tree import ProjectTree
from gui.widgets.tab_manager import TabManager
from gui.events import FileOpenRequest

# Import nowych widgetów
from gui.process_manager import ProcessManager
from gui.widgets.logs_section import LogsSection
from gui.widgets.prompt_section import ScenarioPromptSection
from gui.widgets.process_footer import ProcessFooter
from gui.widgets.main_content_panel import MainContentPanel

class FolderContentView(Static):
    """Placeholder dla folder content - może zostać rozwinięte później"""
    def compose(self) -> ComposeResult:
        yield Static("FolderContentView Widget", id="folder-placeholder")

class AgentDashboard(App):
    """Główna aplikacja GUI z Process Manager"""
    
    DEFAULT_CSS = """
    Screen {
        layout: vertical;
    }
    
    #editor-section {
        height: 4fr;
        min-height: 10;
        width: 100%;
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
    
    #prompt-panel {
        height: 1fr;
        background: transparent;
        margin: 1;
    }
    
    #interactive-input {
        margin: 0;
    }
    
    .input-label {
        width: auto;
    }
    
    Static {
        margin: 0;
        padding: 0;
    }

    """
    
    def __init__(self):
        super().__init__()
        self.process_manager = ProcessManager()
        
        # Cleanup przy zamykaniu
        atexit.register(self.cleanup)
    
    def compose(self) -> ComposeResult:
        """Komponowanie struktury aplikacji"""
        with Vertical():
            # Sekcja editora - podzielona poziomo na drzewo i główny panel
            with Horizontal(id="editor-section"):
                # Panel drzewa plików z przewijaniem
                with VerticalScroll(id="tree-panel"):
                    yield ProjectTree()
                
                # MainContentPanel z zakładkami Logi/Editor
                with VerticalScroll(id="content-panel"):
                    yield MainContentPanel(self.process_manager)
            
            # Sekcja głównego promptu
            with VerticalScroll(id="prompt-panel"):
                yield ScenarioPromptSection(self.process_manager)
            
            # Footer z mikroskopijnymi kontrolkami
            yield ProcessFooter(self.process_manager)

    def on_file_open_request(self, event: FileOpenRequest) -> None:
        """Obsługuje żądanie otwarcia pliku"""
        main_panel = self.query_one(MainContentPanel)
        tab_manager = main_panel.get_tab_manager()
        tab_manager.open_file(event.file_path)
    
    def on_scenario_prompt_section_prompt_submitted(self, event) -> None:
        """Obsługuje wysłanie promptu do interactive loop"""
        # Tutaj możesz dodać dodatkową logikę po wysłaniu promptu
        self.process_manager._emit_log("manager", f"Prompt wysłany do agenta: {event.prompt}")

    def on_mount(self) -> None:
        """Inicjalizacja po uruchomieniu"""
        self.theme = "gruvbox"
        
        # Powitanie w logach
        self.process_manager._emit_log("manager", "🚀 GUI uruchomione - gotowe do sterowania procesami!")
        
        # Automatyczne uruchomienie wszystkich procesów
        self.process_manager._emit_log("manager", "🔄 Automatyczne uruchamianie procesów...")
        self.set_timer(1.0, lambda: self.process_manager.start_all())

    def cleanup(self):
        """Cleanup przy zamykaniu aplikacji"""
        if hasattr(self, 'process_manager'):
            self.process_manager.stop_all()

    def on_exit(self):
        """Wywoływane przy zamykaniu aplikacji"""
        self.cleanup()

def main():
    """Entry point"""
    app = AgentDashboard()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Zamykanie aplikacji...")
    finally:
        if hasattr(app, 'process_manager'):
            app.cleanup()

if __name__ == "__main__":
    main()