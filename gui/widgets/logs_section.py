"""
Sekcja logów - z TextArea zamiast RichLog
"""
import time
from datetime import datetime
from textual.widgets import Static, TextArea
from textual.containers import Vertical
from textual.app import ComposeResult

from gui.process_manager import ProcessManager, LogEntry

class LogsSection(Static):
    """Widget do wyświetlania logów z procesów - z text selection"""
    
    def __init__(self, process_manager: ProcessManager):
        super().__init__()
        self.process_manager = process_manager
        self.pending_logs = []  # Kolejka logów czekających na mount
        self.ready = False
        self.log_text = ""  # Bufor tekstowy
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield TextArea(
                text="",
                read_only=True,
                show_line_numbers=False,
                id="logs-display",
                soft_wrap=True,
                compact=True,
            )
    
    def on_button_pressed(self, event):
        """Obsługa przycisków"""
        if event.button.id == "copy-logs":
            self.copy_all_logs()
    
    def copy_all_logs(self):
        """Kopiuje wszystkie logi do schowka"""
        try:
            import pyperclip
            pyperclip.copy(self.log_text)
            self.app.notify("📋 Logi skopiowane do schowka!")
        except ImportError:
            self.app.notify("❌ Zainstaluj pyperclip: pip install pyperclip", severity="error")
        except Exception as e:
            self.app.notify(f"❌ Błąd kopiowania: {e}", severity="error")
    
    def on_mount(self):
        """Rejestruje handler logów po zamontowaniu"""
        self.ready = True
        
        # Dodaj zaległe logi
        for log in self.pending_logs:
            self._add_log_to_display(log)
        self.pending_logs.clear()
        
        self.process_manager.add_log_handler(self.add_log)
        # Timer do odświeżania logów (jako backup)
        self.set_interval(1.0, self.refresh_logs)
    
    def add_log(self, log_entry: LogEntry):
        """Dodaje nowy log do wyświetlania"""
        if not self.ready:
            # Widget jeszcze nie zamontowany - dodaj do kolejki
            self.pending_logs.append(log_entry)
            return
        
        self._add_log_to_display(log_entry)
    
    def _add_log_to_display(self, log_entry: LogEntry):
        """Dodaje log do TextArea (tylko po mount)"""
        try:
            logs_display = self.query_one("#logs-display", TextArea)
            
            # Formatuj timestamp z float
            time_str = datetime.fromtimestamp(log_entry.timestamp).strftime("%H:%M:%S")
            
            # Ikony dla różnych źródeł (bez Rich markup)
            icons = {
                "agent": "🤖",
                "analyser": "🔍", 
                "synthetiser": "🔧",
                "manager": "⚙️"
            }
            
            icon = icons.get(log_entry.source, "📝")
            
            # Formatuj bez Rich markup (plain text)
            formatted_message = f"[{time_str}] {icon} {log_entry.source.upper()}: {log_entry.message}"
            
            # Dodaj do bufora
            self.log_text += formatted_message + "\n"
            
            # Update TextArea
            logs_display.text = self.log_text
            
            # Auto-scroll do końca
            logs_display.scroll_end(animate=False)
            
        except Exception as e:
            # Fallback - po cichu ignoruj błędy
            pass
    
    def refresh_logs(self):
        """Timer - odświeża logi co sekundę"""
        try:
            # Sprawdź czy są logi w kolejce managera
            manager_logs = self.process_manager.get_logs()
            for log in manager_logs:
                self.add_log(log)
        except Exception:
            pass