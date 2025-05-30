"""
LogsSectionRichLog - widget do wyświetlania logów z GlobalLogHub
"""
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, RichLog
from textual.reactive import reactive
from rich.text import Text
from typing import Optional, List

# Import nowego systemu logowania
from logger import get_log_hub, LogLevel, LogEntry
from logger import CompactFormatter


class LogsSectionRichLog(Vertical):
    """Sekcja wyświetlająca logi z GlobalLogHub"""
    
    DEFAULT_CSS = """
    LogsSectionRichLog {
        height: 1fr;
        width: 100%;
        padding: 0;
        margin: 0;
    }
    
    #logs-container {
        height: 1fr;
        width: 100%;
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 0;
    }
    
    #logs-display {
        height: 1fr;
        width: 100%;
        padding: 0 1;
        background: $surface;
    }
    
    #logs-header {
        height: auto;
        width: 100%;
        background: $surface;
        padding: 0 1;
        text-style: bold;
    }
    """
    
    # Reactive variables
    auto_scroll = reactive(True)
    current_filter_module = reactive("")
    current_filter_level = reactive("")
    
    def __init__(self, process_manager=None):
        super().__init__()
        
        # Zachowaj referencję dla kompatybilności wstecznej
        self.process_manager = process_manager
        
        # Nowy system logowania
        self.log_hub = get_log_hub()
        self.formatter = CompactFormatter()
        
        # Stan lokalny
        self.displayed_logs: List[LogEntry] = []
        self.max_displayed_logs = 500
        
    def compose(self) -> ComposeResult:
        """Komponowanie widgetu"""
        with VerticalScroll(id="logs-container"):
            yield Static("📋 Logi systemowe", id="logs-header")
            yield RichLog(
                highlight=True,
                markup=True,
                auto_scroll=True,
                wrap=True,
                id="logs-display"
            )
    
    def on_mount(self) -> None:
        """Inicjalizacja po zamontowaniu"""
        # Podłącz się jako listener do GlobalLogHub
        self.log_hub.add_listener(self._on_new_log_entry)
        
        # Załaduj istniejące logi
        self._load_existing_logs()
        
        # Kompatybilność wsteczna - jeśli jest process_manager
        if self.process_manager:
            try:
                self.process_manager.add_log_listener(self._on_legacy_log)
            except AttributeError:
                pass
    
    def _on_new_log_entry(self, entry: LogEntry) -> None:
        """Callback dla nowych logów z GlobalLogHub"""
        # Sprawdź filtry
        if not self._should_display_entry(entry):
            return
        
        # Dodaj do lokalnej listy
        self.displayed_logs.append(entry)
        
        # Ogranicz liczbę wyświetlanych logów
        if len(self.displayed_logs) > self.max_displayed_logs:
            self.displayed_logs = self.displayed_logs[-self.max_displayed_logs:]
        
        # Wyświetl w RichLog
        self._display_log_entry(entry)
    
    def _on_legacy_log(self, log_message) -> None:
        """Kompatybilność wsteczna - DEPRECATED"""
        pass
    
    def _should_display_entry(self, entry: LogEntry) -> bool:
        """Sprawdź czy log powinien być wyświetlony (filtry)"""
        # Filtr modułu
        if self.current_filter_module and entry.module != self.current_filter_module:
            return False
        
        # Filtr poziomu
        if self.current_filter_level and entry.level.value != self.current_filter_level:
            return False
        
        return True
    
    def _display_log_entry(self, entry: LogEntry) -> None:
        """Wyświetl pojedynczy log w RichLog"""
        rich_log = self.query_one("#logs-display", RichLog)
        
        # Formatuj log
        formatted_text = self.formatter.format_entry(entry)
        
        # Konwertuj na Rich Text z kolorami
        rich_text = self._create_rich_text(entry, formatted_text)
        
        # Dodaj do RichLog
        rich_log.write(rich_text)
    
    def _create_rich_text(self, entry: LogEntry, formatted_text: str) -> Text:
        """Tworzy Rich Text z kolorami dla log entry"""
        text = Text()
        
        # Kolor bazujący na poziomie loga
        level_colors = {
            LogLevel.DEBUG: "dim white",
            LogLevel.INFO: "white",
            LogLevel.WARN: "yellow",
            LogLevel.ERROR: "red"
        }
        
        # Kolor bazujący na module
        module_colors = {
            "MANAGER": "blue",
            "AGENT": "green", 
            "SYNTHETISER": "yellow",
            "GUI": "purple"
        }
        
        color = level_colors.get(entry.level, "white")
        
        # Dodaj tekst z kolorami
        parts = formatted_text.split('] ', 1)
        if len(parts) == 2:
            # Timestamp i część przed ]
            text.append(parts[0] + '] ', style="dim")
            
            # Reszta z kolorem poziomu
            text.append(parts[1], style=color)
        else:
            text.append(formatted_text, style=color)
        
        return text
    
    def _load_existing_logs(self) -> None:
        """Załaduj istniejące logi z hub'a"""
        existing_logs = self.log_hub.get_logs(limit=100)
        
        for entry in existing_logs:
            if self._should_display_entry(entry):
                self.displayed_logs.append(entry)
                self._display_log_entry(entry)
    
    def clear_logs(self) -> None:
        """Wyczyść wyświetlane logi"""
        rich_log = self.query_one("#logs-display", RichLog)
        rich_log.clear()
        self.displayed_logs.clear()
    
    def export_logs(self, format: str = "txt") -> str:
        """Eksportuj logi do różnych formatów"""
        if format == "txt":
            return "\n".join([self.formatter.format_entry(entry) for entry in self.displayed_logs])
        elif format == "json":
            from logger import JSONFormatter
            json_formatter = JSONFormatter()
            return "\n".join([json_formatter.format_entry(entry) for entry in self.displayed_logs])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def on_key(self, event) -> None:
        """Obsługa skrótów klawiszowych"""
        if event.key == "ctrl+c":
            # Kopiuj wszystkie logi
            self._copy_logs_to_clipboard()
            event.prevent_default()
        elif event.key == "ctrl+l":
            # Wyczyść logi
            self.clear_logs()
            event.prevent_default()
    
    def _copy_logs_to_clipboard(self) -> None:
        """Kopiuj logi do clipboard"""
        try:
            # Pobierz wszystkie wyświetlane logi jako tekst
            logs_text = self.export_logs(format="txt")
            
            # Spróbuj skopiować do clipboard
            import pyperclip
            pyperclip.copy(logs_text)
            
            # Powiadom użytkownika
            self.notify("📋 Logi skopiowane do schowka!", severity="information")
            
        except ImportError:
            # Jeśli pyperclip nie jest dostępne, zapisz do pliku
            self._save_logs_to_file()
        except Exception as e:
            self.notify(f"❌ Błąd kopiowania: {e}", severity="error")
    
    def _save_logs_to_file(self) -> None:
        """Zapisz logi do pliku jako backup"""
        try:
            from pathlib import Path
            from datetime import datetime
            
            # Nazwa pliku z timestampem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_export_{timestamp}.txt"
            filepath = Path(filename)
            
            # Zapisz logi
            logs_text = self.export_logs(format="txt")
            filepath.write_text(logs_text, encoding="utf-8")
            
            self.notify(f"📄 Logi zapisane do {filename}", severity="information")
            
        except Exception as e:
            self.notify(f"❌ Błąd zapisu: {e}", severity="error")
    
    def on_unmount(self) -> None:
        """Cleanup przy odmontowywaniu"""
        try:
            self.log_hub.remove_listener(self._on_new_log_entry)
        except:
            pass
        
        if self.process_manager:
            try:
                self.process_manager.remove_log_listener(self._on_legacy_log)
            except:
                pass