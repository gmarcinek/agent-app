"""
Main Prompt Section Widget
Section 4: Main Prompt (100% width, 200px height)
"""

from textual.widgets import Static, Input, Button
from textual.containers import Container, Horizontal
from textual.app import ComposeResult


class MainPromptSection(Static):  
    """Global prompt input and controls component"""
    
    CSS = """
    #main-prompt-section {
        height: 12;
        padding: 1;
        border-top: solid $primary;
        layout: vertical;
    }

    #main-prompt-container {
        layout: horizontal;
        height: auto;
        margin: 1 0;
    }

    #main-prompt {
        width: 1fr;
        margin-right: 1;
        height: 3;
    }

    #main-buttons {
        layout: horizontal;
        width: auto;
    }

    #main-send, #main-reset {
        width: 10;
        max-width: 10;
        height: 3;
        margin: 0 1;
        padding: 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="main-prompt-section"):
            yield Static("💬 Global Agent Prompt", id="main-prompt-title")
            
            with Horizontal(id="main-prompt-container"):
                yield Input(placeholder="Enter main goal/prompt...", id="main-prompt")
                
                with Container(id="main-buttons"):
                    yield Button("🚀 Send", id="main-send", variant="success")
                    yield Button("🔄 Reset", id="main-reset", variant="error")