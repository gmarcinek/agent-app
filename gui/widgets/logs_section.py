"""
Logs Section Widget
Section 3: Logs (100% width, 3 lines)
"""

from textual.widgets import Static
from textual.app import ComposeResult


class LogsSection(Static):
    """Compact logs display component"""
    
    CSS = """
    #logs {
        height: 3;
        background: $surface;
        padding: 0 1;
        border-top: solid $primary;
        text-style: italic;
    }
    """
    
    def compose(self) -> ComposeResult:
        logs = "🧠[12:34] Knowledge updated (13 files) • 🔍[12:35] File change: App.tsx • ✅[12:36] Scenario completed • 🤖[12:37] Ready"
        yield Static(logs, id="logs")