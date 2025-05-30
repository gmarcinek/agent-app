from pathlib import Path
from typing import Dict, Optional, Tuple, List, Set
from textual.containers import Vertical
from textual.widgets import TabbedContent, TabPane, Static
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from gui.widgets.file_view import FileView


class TabManager(Vertical):
    """Zarządza wieloma otwartymi plikami w tabach"""
    
    DEFAULT_CSS = """
    .tab-container Tab {
        margin-right: 1;
        padding: 0 1;
    }
    
    .file-tab {
    }
    
    .welcome-tab {
    }
    
    .welcome-message {
        /* Wiadomość w welcome tabie */
        content-align: center middle;
        width: 100%;
        height: 100%;
    }

    .modified-tab {
        color: yellow;
    }
    """

    BINDINGS = [
        Binding("ctrl+w", "close_active_tab", "Close Tab", priority=True),
    ]

    class FileModified(Message):
        """Wiadomość informująca o modyfikacji pliku"""
        def __init__(self, file_path: Path, modified: bool) -> None:
            self.file_path = file_path
            self.modified = modified
            super().__init__()

    def __init__(self) -> None:
        super().__init__()
        self.open_files: Dict[Path, Tuple[str, FileView]] = {}
        self.active_file: Optional[Path] = None
        self.modified_files: Set[Path] = set()

    def compose(self) -> ComposeResult:
        with TabbedContent(id="file-tabs", classes="tab-container") as tabbed:
            welcome_pane = TabPane("Welcome", Static("📄 Select a file to open", classes="welcome-message"), id="welcome-tab")
            welcome_pane.add_class("welcome-tab")
            yield welcome_pane

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
            
        try:
            # Stwórz nowy FileView dla tego pliku
            file_view = FileView(file_path)
            
            # Podłącz obsługę zdarzeń od FileView
            file_view.watch_modified(self._on_file_modified)
            
            # Dodaj nowy tab
            tabbed = self.query_one(TabbedContent)
            tab_name = file_path.name
            
            # Generuj unikalny ID dla taba (prosty numer)
            tab_id = f"file_tab_{len(self.open_files)}"
            
            tab_pane = TabPane(tab_name, file_view, id=tab_id)
            tab_pane.add_class("file-tab")
            tabbed.add_pane(tab_pane)
            
            # Zapisz ID taba razem z FileView
            self.open_files[file_path] = (tab_id, file_view)
            
            # Przełącz focus na nowo utworzony tab
            tabbed.active = tab_id
            self.active_file = file_path
        except Exception as e:
            self.notify(f"Błąd podczas otwierania pliku: {e}", severity="error")

    def _on_file_modified(self, file_path: Path, modified: bool) -> None:
        """Obsługuje zdarzenie modyfikacji pliku"""
        if modified:
            self.modified_files.add(file_path)
        else:
            self.modified_files.discard(file_path)
        
        # Aktualizuj wizualny stan taba
        self._update_tab_modified_state(file_path, modified)
        
        # Wyślij wiadomość o modyfikacji
        self.post_message(self.FileModified(file_path, modified))

    def _update_tab_modified_state(self, file_path: Path, modified: bool) -> None:
        """Aktualizuje wygląd taba w zależności od stanu modyfikacji"""
        if file_path not in self.open_files:
            return
            
        tab_id, _ = self.open_files[file_path]
        tabbed = self.query_one(TabbedContent)
        
        # Znajdź tab odpowiadający plikowi
        for tab in tabbed.query("Tab"):
            if tab.id == tab_id:
                if modified:
                    tab.add_class("modified-tab")
                    # Dodaj gwiazdkę do nazwy taba
                    if not tab.label.endswith("*"):
                        tab.label = f"{tab.label}*"
                else:
                    tab.remove_class("modified-tab")
                    # Usuń gwiazdkę z nazwy
                    if tab.label.endswith("*"):
                        tab.label = tab.label[:-1]
                break

    def close_file(self, file_path: Path) -> None:
        """Zamyka tab z plikiem bez pytania o zapisanie zmian"""
        if file_path not in self.open_files:
            return
            
        tab_id, file_view = self.open_files[file_path]
        
        # Usuń z mapy i zbioru zmodyfikowanych
        del self.open_files[file_path]
        self.modified_files.discard(file_path)
        
        # Odłącz obserwowanie zdarzeń
        file_view.unwatch_modified(self._on_file_modified)
        
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

    def save_file(self, file_path: Path) -> bool:
        """Zapisuje zawartość pliku"""
        if file_path not in self.open_files:
            return False
            
        _, file_view = self.open_files[file_path]
        try:
            # Zapisz zawartość
            success = file_view.save()
            if success:
                # Usuń z listy zmodyfikowanych
                self.modified_files.discard(file_path)
                # Aktualizuj stan taba
                self._update_tab_modified_state(file_path, False)   
            return success
        except Exception as e:
            self.notify(f"Błąd podczas zapisywania pliku: {e}", severity="error")
            return False

    def refresh_file(self, file_path: Path) -> bool:
        """Odświeża zawartość pliku z dysku"""
        if file_path not in self.open_files:
            return False
            
        _, file_view = self.open_files[file_path]
        try:
            # Odśwież zawartość
            success = file_view.reload_from_disk()
            if success:
                # Usuń z listy zmodyfikowanych
                self.modified_files.discard(file_path)
                # Aktualizuj stan taba
                self._update_tab_modified_state(file_path, False)
                self.notify(f"Odświeżono plik: {file_path.name}")
            return success
        except Exception as e:
            self.notify(f"Błąd podczas odświeżania pliku: {e}", severity="error")
            return False

    def on_key(self, event) -> None:
        """Przechwytuj klawisze bezpośrednio"""
        if event.key == "ctrl+w":
            if self.active_file:
                self.close_file(self.active_file)
                event.prevent_default()
                event.stop()
        elif event.key == "ctrl+s":
            if self.active_file:
                self.save_file(self.active_file)
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
                # Daj focus dla FileView
                file_view.focus()
                return

    def get_active_file_view(self) -> Optional[FileView]:
        """Zwraca aktywny FileView"""
        if self.active_file and self.active_file in self.open_files:
            _, file_view = self.open_files[self.active_file]
            return file_view
        return None

    def get_open_files_list(self) -> List[Path]:
        """Zwraca listę otwartych plików"""
        return list(self.open_files.keys())

    def get_modified_files_list(self) -> List[Path]:
        """Zwraca listę zmodyfikowanych plików"""
        return list(self.modified_files)

    def save_all_files(self) -> None:
        """Zapisuje wszystkie zmodyfikowane pliki"""
        for file_path in list(self.modified_files):
            self.save_file(file_path)