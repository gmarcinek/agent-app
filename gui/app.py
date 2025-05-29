from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static
from gui.widgets.project_tree import ProjectTree
from gui.widgets.file_content import FileContentView

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
        height: 1fr;
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
        margin: 0 0 0 1;
        padding: 1;
        background: $surface;
    }
    
    LogsSection {
        margin: 0;
    }

    #log-panel {
        height: 4;
        min-height: 2;
        background: $surface;
        padding: 1;
        background: $surface;
        margin: 1 0 1 0;
        padding: 1;
    }
    
    MainPromptSection {
        margin: 0;
    }

    #prompt-panel {
        height: 10;
        min-height: 20%;
        padding: 1;
        background: $surface;
        padding: 1;
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
        with Vertical():
            # Section 2: Editor (resizable horizontal)
            with Horizontal(id="editor-section"):
                # Tree panel
                with Container(id="tree-panel"):
                    yield ProjectTree()
                
                # Content panel
                with Static(id="content-panel"):
                    yield FileContentView()
            
            # Section 3: Logs (resizable from top)
            with Container(id="log-panel"):
                yield LogsSection()
            
            # Section 4: Main Prompt (resizable from logs)
            with Container(id="prompt-panel"):
                yield MainPromptSection()

    def on_mount(self) -> None:
        """Po uruchomieniu pokaż placeholder w file viewer"""
        self.theme = "gruvbox"
        file_viewer = self.query_one(FileContentView)
        file_viewer.show_placeholder()

def main():
    """Entry point"""
    app = AgentDashboard()
    app.run()


if __name__ == "__main__":
    main()