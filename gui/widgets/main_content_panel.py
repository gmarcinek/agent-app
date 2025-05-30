"""
MainContentPanel - główny panel z zakładkami Logi A/B Test/Editor
"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import TabbedContent, TabPane, Static
from gui.widgets.tab_manager import TabManager
from gui.widgets.logs_section import LogsSection as LogsSectionTextArea
from gui.widgets.logs_section_richlog import LogsSectionRichLog

class MainContentPanel(Container):
    """Panel główny z zakładkami Logi A/B Test i Editor"""
    
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
    
    .logs-textarea-tab {
    }
    
    .logs-richlog-tab {
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
        with TabbedContent(initial="logs-textarea", classes="main-tab-container") as tabbed:
            # Zakładka z logami - TextArea
            logs_textarea_pane = TabPane("📝 Logi (TextArea)", id="logs-textarea")
            logs_textarea_pane.add_class("logs-textarea-tab")
            yield logs_textarea_pane
            
            # Zakładka z logami - RichLog
            logs_richlog_pane = TabPane("🎨 Logi (RichLog)", id="logs-richlog")
            logs_richlog_pane.add_class("logs-richlog-tab")
            yield logs_richlog_pane
            
            # Zakładka z edytorem
            editor_pane = TabPane("📄 Editor", id="editor")
            editor_pane.add_class("editor-tab")
            yield editor_pane
    
    def on_mount(self) -> None:
        """Inicjalizacja po zamontowaniu - dodaj content do tabów"""
        # Dodaj LogsSection TextArea do pierwszej zakładki
        logs_textarea_pane = self.query_one("#logs-textarea", TabPane)
        logs_textarea_pane.mount(LogsSectionTextArea(self.process_manager))
        
        # Dodaj LogsSection RichLog do drugiej zakładki
        logs_richlog_pane = self.query_one("#logs-richlog", TabPane)
        logs_richlog_pane.mount(LogsSectionRichLog(self.process_manager))
        
        # Dodaj TabManager do zakładki Editor
        editor_pane = self.query_one("#editor", TabPane)
        editor_pane.mount(TabManager())
        
        # Ustaw domyślną zakładkę na TextArea Logi
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "logs-textarea"
    
    def get_tab_manager(self) -> TabManager:
        """Zwraca TabManager dla dostępu z zewnątrz"""
        return self.query_one(TabManager)