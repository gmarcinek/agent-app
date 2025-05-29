from pathlib import Path
from typing import Dict, Optional, Tuple
from textual.containers import Vertical
from textual.widgets import TabbedContent, TabPane, Static
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Mount
from gui.widgets.file_view import FileView

class TabManager(Vertical):
    """Zarządza wieloma otwartymi plikami w tabach"""

    BINDINGS = [
        Binding("ctrl+w", "close_active_tab", "Close Tab", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.open_files: Dict[Path, Tuple[str, FileView]] = {}
        self.active_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        with TabbedContent(id="file-tabs") as tabbed:
            yield TabPane("Welcome", Static("📄 Select a file to open", classes="message"), id="welcome-tab")

    def on_mount(self) -> None:
        """Inicjalizacja po zamontowaniu widgetu"""
        # Ustaw welcome tab jako aktywny na początku
        tabbed = self.query_one(TabbedContent)
        if tabbed.tab_count > 0:
            tabbed.active = "welcome-tab"

    def open_file(self, file_path: Path) -> None:
        """Otwiera plik w nowym tabie lub przełącza na istniejący"""
        
        # Sprawdź czy plik już otwarty
        if file_path in self.open_files:
            tab_id, file_view = self.open_files[file_path]
            tabbed = self.query_one(TabbedContent)
            tabbed.active = tab_id
            self.active_file = file_path
            return
            
        # Stwórz nowy FileView dla tego pliku
        file_view = FileView(file_path)
        
        # Dodaj nowy tab
        tabbed = self.query_one(TabbedContent)
        tab_name = file_path.name
        
        # Generuj unikalny ID dla taba (prosty numer)
        tab_id = f"file_tab_{len(self.open_files)}"
        
        tab_pane = TabPane(tab_name, file_view, id=tab_id)
        tabbed.add_pane(tab_pane)
        
        # Zapisz ID taba razem z FileView
        self.open_files[file_path] = (tab_id, file_view)
        
        # Przełącz focus na nowo utworzony tab
        tabbed.active = tab_id
        self.active_file = file_path

    def close_file(self, file_path: Path) -> None:
        """Zamyka tab z plikiem"""
        if file_path not in self.open_files:
            return
            
        tab_id, file_view = self.open_files[file_path]
        
        # Usuń z mapy
        del self.open_files[file_path]
        
        # Usuń TabPane z TabbedContent
        tabbed = self.query_one(TabbedContent)
        try:
            # Znajdź i usuń tab pane
            for tab_pane in tabbed.query(TabPane):
                if tab_pane.id == tab_id:
                    tabbed.remove_pane(tab_pane.id)
                    break
        except Exception as e:
            self.log.warning(f"Błąd podczas usuwania taba: {e}")
        
        # Jeśli to był aktywny plik, przełącz na inny
        if self.active_file == file_path:
            remaining_files = list(self.open_files.keys())
            if remaining_files:
                # Przełącz na ostatni plik
                last_file = remaining_files[-1]
                last_tab_id, _ = self.open_files[last_file]
                tabbed.active = last_tab_id
                self.active_file = last_file
            else:
                # Przełącz na welcome tab jeśli nie ma więcej plików
                tabbed.active = "welcome-tab"
                self.active_file = None

    def on_key(self, event) -> None:
        """Przechwytuj klawisze bezpośrednio"""
        if event.key == "ctrl+w":
            if self.active_file:
                self.close_file(self.active_file)
                event.prevent_default()
                event.stop()

    def action_close_active_tab(self) -> None:
        """Zamyka aktywny tab (Ctrl+W)"""
        if self.active_file:
            self.close_file(self.active_file)

    def on_tabbed_content_tab_activated(self, event) -> None:
        """Obsłuż przełączenie taba - aktualizuj active_file"""
        active_tab_id = event.tab.id
        
        # Sprawdź czy to welcome tab
        if active_tab_id == "welcome-tab":
            self.active_file = None
            return
        
        # Znajdź który plik odpowiada aktywnemu tabowi
        for file_path, (tab_id, file_view) in self.open_files.items():
            if tab_id == active_tab_id:
                self.active_file = file_path
                return

    # Middle mouse nie jest niezawodny w Textual, używamy Ctrl+W

    def get_active_file_view(self) -> Optional[FileView]:
        """Zwraca aktywny FileView"""
        if self.active_file and self.active_file in self.open_files:
            _, file_view = self.open_files[self.active_file]
            return file_view
        return None

    def get_open_files_list(self) -> list[Path]:
        """Zwraca listę otwartych plików"""
        return list(self.open_files.keys())

    def close_all_files(self) -> None:
        """Zamyka wszystkie otwarte pliki"""
        files_to_close = list(self.open_files.keys())
        for file_path in files_to_close:
            self.close_file(file_path)