import json
from datetime import datetime
from pathlib import Path
from textual.widgets import Static, TextArea, Button, Input, Label
from textual.containers import Horizontal, Vertical, Container
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive

from gui.process_manager import ProcessManager, LogEntry

class ScenarioPromptSection(Static):
    """Widget do wprowadzania promptów dla interactive loop agenta"""

    def __init__(self, process_manager: ProcessManager):
        super().__init__()
        self.process_manager = process_manager
    
    class PromptSubmitted(Message):
        """Wiadomość wysyłana gdy użytkownik wyśle prompt"""
        def __init__(self, prompt: str):
            super().__init__()
            self.prompt = prompt
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(
                placeholder="Wpisz co agent ma zrobić i naciśnij Enter...",
                id="interactive-input"
            )
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Obsługa Enter - wysłanie promptu do interactive loop"""
        if event.input.id == "interactive-input":
            self.submit_interactive_prompt()
    
    def submit_interactive_prompt(self):
        """Wysyła prompt bezpośrednio do interactive loop agenta"""
        prompt_input = self.query_one("#interactive-input", Input)
        
        prompt = prompt_input.value.strip()
        if not prompt:
            self.notify("⚠️ Wprowadź prompt!", severity="warning")
            return
        
        try:
            # Wyślij prompt bezpośrednio do agenta przez stdin
            if self.process_manager.send_to_agent(prompt):
                self.notify(f"📨 Prompt wysłany: {prompt[:50]}...")
                
                # Wyczyść input
                prompt_input.value = ""
                
                # Wyemituj event dla App
                self.post_message(self.PromptSubmitted(prompt))
            else:
                self.notify("❌ Agent nie odpowiada - może nie działa?", severity="error")
                
        except Exception as e:
            self.notify(f"❌ Błąd wysyłania: {e}", severity="error")