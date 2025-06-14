"""
LogsSection - widget do wyświetlania logów z GlobalLogHub
"""
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, TextArea
from textual.reactive import reactive
from typing import Optional, List

# Import nowego systemu logowania
from logger import get_log_hub, LogLevel, LogEntry
from logger import CompactFormatter


class LogsSection(Vertical):
    """Sekcja wyświetlająca logi z GlobalLogHub"""
    
    DEFAULT_CSS = """
    LogsSection {
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
        padding: 1;
        background: $surface;
        scrollbar-size-vertical: 1;
        scrollbar-size-horizontal: 0;
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
            yield TextArea(
                text="",
                read_only=True,
                show_line_numbers=False,
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
            # Odśwież display gdy przekroczymy limit
            self._refresh_display_from_memory()
        
        # Wyświetl w TextArea
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
        """Wyświetl pojedynczy log w TextArea"""
        text_area = self.query_one("#logs-display", TextArea)
        
        # Formatuj log jako zwykły tekst
        formatted_text = self.formatter.format_entry(entry)
        
        # Dodaj do TextArea
        current_text = text_area.text
        if current_text:
            text_area.text = current_text + "\n" + formatted_text
        else:
            text_area.text = formatted_text
        
        # Auto-scroll do końca jeśli włączone
        if self.auto_scroll:
            text_area.cursor_position = len(text_area.text)
    
    def _load_existing_logs(self) -> None:
        """Załaduj istniejące logi z hub'a"""
        existing_logs = self.log_hub.get_logs(limit=100)
        
        for entry in existing_logs:
            if self._should_display_entry(entry):
                self.displayed_logs.append(entry)
                self._display_log_entry(entry)
    
    def _refresh_display_from_memory(self) -> None:
        """Odśwież wyświetlanie z pamięci (np. po przekroczeniu limitu)"""
        text_area = self.query_one("#logs-display", TextArea)
        
        # Zbuduj tekst z displayed_logs
        log_lines = []
        for entry in self.displayed_logs:
            if self._should_display_entry(entry):
                formatted_text = self.formatter.format_entry(entry)
                log_lines.append(formatted_text)
        
        # Ustaw cały tekst naraz
        text_area.text = "\n".join(log_lines)
        
        # Auto-scroll do końca
        if self.auto_scroll:
            text_area.cursor_position = len(text_area.text)
    
    # Metody filtrowania
    def filter_by_module(self, module: str) -> None:
        """Filtruj logi według modułu"""
        self.current_filter_module = module
        self._refresh_display_from_memory()
    
    def filter_by_level(self, level: str) -> None:
        """Filtruj logi według poziomu"""
        self.current_filter_level = level
        self._refresh_display_from_memory()
    
    def clear_filters(self) -> None:
        """Wyczyść wszystkie filtry"""
        self.current_filter_module = ""
        self.current_filter_level = ""
        self._refresh_display_from_memory()
    
    def clear_logs(self) -> None:
        """Wyczyść wyświetlane logi"""
        text_area = self.query_one("#logs-display", TextArea)
        text_area.text = ""
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
    
    def toggle_auto_scroll(self) -> None:
        """Przełącz auto-scroll"""
        self.auto_scroll = not self.auto_scroll
    
    def on_key(self, event) -> None:
        """Obsługa skrótów klawiszowych"""
        if event.key == "ctrl+l":
            # Wyczyść logi (Ctrl+L jak w terminalu)
            self.clear_logs()
            event.prevent_default()
        # Ctrl+C i Ctrl+A są obsługiwane natywnie przez TextArea
    
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