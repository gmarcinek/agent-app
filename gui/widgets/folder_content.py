"""
Folder Content View Widget - tylko prawdziwy content
"""

from textual.widgets import Static, TextArea, Input, Button
from textual.containers import Container, Horizontal
from textual.app import ComposeResult


class FolderContentView(Static):
    """Folder content viewer and module manager component - pokazuje tylko prawdziwy content"""
    
    CSS = """
    #folder-title {
        background: $accent;
        padding: 0 1;
        text-style: bold;
        height: 3;
    }

    #folder-content {
        height: 1fr;
        border: solid $primary;
        margin: 1 0;
    }

    #folder-prompt-section {
        layout: vertical;
        height: auto;
        margin: 1 0;
    }

    #folder-actions {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }

    #folder-prompt {
        margin: 0 0 1 0;
        height: 3;
    }

    #folder-rebuild {
        width: 12;
        max-width: 12;
        height: 3;
        margin: 0 1;
        padding: 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        # Folder title - na start puste
        yield Static("📂 No folder selected", id="folder-title")
        
        # Module summary - na start puste
        yield TextArea("", id="folder-content")
        
        # Folder-specific prompt section
        with Container(id="folder-prompt-section"):
            yield Input(placeholder="Enter module-level prompt...", id="folder-prompt")
            with Horizontal(id="folder-actions"):
                yield Button("🏗️ Rebuild Module", id="folder-rebuild", variant="primary")
        
        # Metadata bar - na start puste
        yield Static("Select a folder to view summary", id="file-metadata")
    
    def update_content(self, title: str, summary: str, dir_path=None):
        """Aktualizuje zawartość widoku folderu"""
        try:
            # Update title
            title_widget = self.query_one("#folder-title")
            title_widget.update(title)
            
            # Update summary
            content_widget = self.query_one("#folder-content", TextArea)
            content_widget.text = summary
            # Zostaw domyślny język dla folderu (plain text)
            
            # Update metadata
            self._update_metadata(summary, dir_path)
            
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"❌ Error updating folder content: {e}", severity="error")
    
    def _update_metadata(self, summary: str, dir_path=None):
        """Aktualizuje pasek metadanych dla folderu"""
        try:
            metadata_widget = self.query_one("#file-metadata")
            
            if not summary and not dir_path:
                metadata_widget.update("Select a folder to view summary")
                return
            
            # Podstawowe statystyki z summary
            lines = len(summary.split('\n')) if summary else 0
            
            # Spróbuj wyciągnąć statystyki z tekstu summary
            file_count = 0
            dir_count = 0
            
            if summary:
                # Szukaj linii z "Total Files:" i "Total Directories:"
                for line in summary.split('\n'):
                    line = line.strip()
                    if line.startswith('Total Files:'):
                        try:
                            file_count = int(line.split(':')[-1].strip())
                        except:
                            pass
                    elif line.startswith('Total Directories:'):
                        try:
                            dir_count = int(line.split(':')[-1].strip())
                        except:
                            pass
            
            # Informacje o folderze
            folder_info = ""
            if dir_path:
                try:
                    from pathlib import Path
                    path = Path(dir_path)
                    folder_info = f"Path: {path.name}/"
                except:
                    folder_info = "Path: Unknown"
            
            # Składaj metadata
            metadata_parts = []
            if file_count > 0:
                metadata_parts.append(f"Files: {file_count}")
            if dir_count > 0:
                metadata_parts.append(f"Dirs: {dir_count}")
            if lines > 0:
                metadata_parts.append(f"Summary Lines: {lines}")
            if folder_info:
                metadata_parts.append(folder_info)
            
            metadata_text = " | ".join(metadata_parts) if metadata_parts else "Empty folder"
            metadata_widget.update(metadata_text)
            
        except Exception as e:
            try:
                metadata_widget = self.query_one("#file-metadata")
                metadata_widget.update(f"Metadata error: {str(e)}")
            except:
                pass
    
    def clear_content(self):
        """Czyści zawartość widoku folderu"""
        try:
            self.query_one("#folder-title").update("📂 No folder selected")
            self.query_one("#folder-content", TextArea).text = ""
            self.query_one("#file-metadata").update("Select a folder to view summary")
        except Exception as e:
            if hasattr(self.app, 'notify'):
                self.app.notify(f"❌ Error clearing folder content: {e}", severity="error")
    
    def get_summary(self) -> str:
        """Zwraca aktualny summary folderu"""
        try:
            return self.query_one("#folder-content", TextArea).text
        except:
            return ""