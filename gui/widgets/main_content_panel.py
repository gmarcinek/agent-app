"""
MainContentPanel - główny panel z zakładkami Logi/Editor
"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import TabbedContent, TabPane, Static
from gui.widgets.tab_manager import TabManager
from gui.widgets.logs_section import LogsSection

class MainContentPanel(Container):
    """Panel główny z zakładkami Logi i Editor"""
    
    DEFAULT_CSS = """
    MainContentPanel {
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
    }
    
    .main-tab-container {
        width: 100%;
        height: 100%;
        padding: 0;
        margin: 0;
    }
    
    .main-tab-container Tab {
        margin-right: 1;
        padding: 0 1;
    }
    
    .logs-tab {
    }
    
    .editor-tab {
    }
    
    TabPane {
        padding: 0;
        margin: 0;
    }
    
    TabbedContent > Tabs {
        border: none;
        background: $surface;
    }
    
    TabbedContent > ContentTabs {
        border: none;
        padding: 0;
        margin: 0;
    }
    """
    
    def __init__(self, process_manager):
        super().__init__()
        self.process_manager = process_manager
    
    def compose(self) -> ComposeResult:
        """Komponowanie panelu z zakładkami"""
        with TabbedContent(initial="logs", classes="main-tab-container") as tabbed:
            # Zakładka z logami
            logs_pane = TabPane("Logi", id="logs")
            logs_pane.add_class("logs-tab")
            yield logs_pane
            
            # Zakładka z edytorem
            editor_pane = TabPane("Editor", id="editor")
            editor_pane.add_class("editor-tab")
            yield editor_pane
    
    def on_mount(self) -> None:
        """Inicjalizacja po zamontowaniu - dodaj content do tabów"""
        # Dodaj LogsSection do zakładki Logi
        logs_pane = self.query_one("#logs", TabPane)
        logs_pane.mount(LogsSection(self.process_manager))
        
        # Dodaj TabManager do zakładki Editor
        editor_pane = self.query_one("#editor", TabPane)
        editor_pane.mount(TabManager())
        
        # Ustaw domyślną zakładkę na Logi
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "logs"
        """Zwraca TabManager dla dostępu z zewnątrz"""
        return self.query_one(TabManager)