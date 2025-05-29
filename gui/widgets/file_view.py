from pathlib import Path
from typing import Optional, Callable, List
from textual.widgets import Static, TextArea
from textual.containers import Vertical, Container
from textual.binding import Binding
from textual.message import Message

class FileView(Vertical):
    """Widok pojedynczego pliku - jeden tab"""

    DEFAULT_CSS = """
    .file-header {
        height: auto;
        text-style: bold;
        padding: 0;
        margin-bottom: 1;
    }

    .message {
        padding: 1;
        text-style: italic;
    }

    .editor-wrapper {
        border: hidden;
    }

    TextArea {
        border: none;
        height: 100%;
        background: transparent !important;
    }
    
    .file-footer {
        height: 1;
        background: $surface-darken-1;
        color: $text;
        opacity: 0.5;
        padding: 0 1;
    }
    
    .file-status {
        width: 100%;
        text-align: right;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("f5", "reload", "Reload", priority=True),
    ]
    
    class FileModifiedMessage(Message):
        """Wiadomość o modyfikacji zawartości pliku"""
        def __init__(self, file_path: Path, modified: bool) -> None:
            self.file_path = file_path
            self.modified = modified
            super().__init__()

    def __init__(self, file_path: Path) -> None:
        super().__init__()
        self.file_path = file_path
        self.editor: Optional[TextArea] = None
        self.modified = False
        self._original_content: str = ""
        self._modified_callbacks: List[Callable[[Path, bool], None]] = []
        self.is_valid_text_file = True  # Flaga określająca czy to prawidłowy plik tekstowy
        self.status_bar: Optional[Static] = None
    
    def on_mount(self) -> None:
        """Po zamontowaniu załaduj plik"""
        self._load_file()
        
        # Obserwuj zdarzenia kursora
        if self.editor and self.is_valid_text_file:
            # Używamy watch zamiast cursor_moved.subscribe
            self.watch(self.editor, "cursor_position", self._on_cursor_moved)

    def _load_file(self) -> None:
        """Ładuje zawartość pliku"""
        if not self.file_path.exists():
            self.is_valid_text_file = False
            self.mount(Static("❌ File does not exist", classes="message"))
            return

        if self.file_path.is_dir():
            self.is_valid_text_file = False
            self.mount(Static(f"📁 {self.file_path.name} is a directory", classes="message"))
            return

        if not self._is_text_file(self.file_path):
            self.is_valid_text_file = False
            size = self.file_path.stat().st_size
            self.mount(Static(f"📦 Binary file: {self.file_path.name} ({size:,} bytes)", classes="message"))
            return

        try:
            content = self.file_path.read_text(encoding="utf-8")
            self._original_content = content  # Zapisz oryginalną zawartość
        except Exception as e:
            self.is_valid_text_file = False
            self.mount(Static(f"❌ Error reading file:\n{e}", classes="message"))
            return

        lines = content.count("\n") + 1
        header_text = f"📄 {self.file_path.name} ({lines} lines)"
        self.mount(Container(Static(header_text), classes="file-header"))

        language = self._detect_language(self.file_path)
        
        # Próbuj z różnymi wariantami języka
        language_variants = self._get_language_variants(language)
        editor_created = False
        
        for lang in language_variants:
            try:
                self.editor = TextArea.code_editor(
                    text=content,
                    language=lang,
                    show_line_numbers=True,
                    soft_wrap=True,
                    compact=True,
                )
                
                # Konfiguracja motywu i stylów
                from gui.themes.gruvbox_compatible_theme import gruvbox_transparent_theme
                self.editor.register_theme(gruvbox_transparent_theme)
                self.editor.theme = "gruvbox_transparent"
                self.editor.styles.background = "#3c3836" 
                
                editor_created = True
                break
            except Exception:
                continue
        
        # Jeśli żaden wariant nie zadziałał, użyj podstawowego TextArea
        if not editor_created:
            self.editor = TextArea(
                text=content,
                show_line_numbers=True,
            )
            
            # Konfiguracja motywu i stylów
            from gui.themes.gruvbox_compatible_theme import gruvbox_transparent_theme
            self.editor.register_theme(gruvbox_transparent_theme)
            self.editor.theme = "gruvbox_transparent"
            self.editor.styles.background = "#3c3836"
            
        # Użyj metody watch_text do śledzenia zmian w tekście
        self.watch(self.editor, "value", self._on_text_changed)

        wrapper = Container(self.editor, classes="editor-wrapper")
        self.mount(wrapper)
        
        # Dodaj pasek statusu
        self._add_status_bar()
    
    def _add_status_bar(self) -> None:
        """Dodaje pasek statusu z informacjami o pliku i skrótach"""
        status_text = f"📄 {self.file_path.name} | Ctrl+S: Save | F5: Reload"
        self.status_bar = Static(status_text, classes="file-status")
        footer = Container(self.status_bar, classes="file-footer")
        self.mount(footer)

    def _get_language_variants(self, language: str) -> list[str]:
        """Zwraca listę wariantów nazw języka do wypróbowania."""
        variants = [language]
        
        # Dodaj alternatywne nazwy dla problematycznych języków
        if language == "typescript":
            variants.extend(["ts", "javascript"])
        elif language == "scss":
            variants.extend(["sass", "css"])
        elif language == "yaml":
            variants.extend(["yml"])
        elif language == "bash":
            variants.extend(["shell", "sh"])
        elif language == "dockerfile":
            variants.extend(["docker"])
        
        # Zawsze dodaj "text" jako ostatni fallback
        variants.append("text")
        return variants

    def _is_text_file(self, path: Path) -> bool:
        """Sprawdza czy plik jest plikiem tekstowym"""
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                chunk.decode("utf-8")
            return True
        except Exception:
            return False
            
    def _detect_language(self, path: Path) -> str:
        """Wykrywa język programowania na podstawie rozszerzenia pliku"""
        ext = path.suffix.lower()
        return {
            '.py': 'python',
            '.js': 'javascript', '.jsx': 'javascript',
            '.ts': 'typescript', '.tsx': 'typescript',
            '.html': 'html', '.htm': 'html',
            '.css': 'css', '.scss': 'scss', '.sass': 'sass',
            '.json': 'json',
            '.yaml': 'yaml', '.yml': 'yaml',
            '.xml': 'xml',
            '.sql': 'sql',
            '.md': 'markdown',
            '.sh': 'bash', '.bash': 'bash',
            '.dockerfile': 'dockerfile',
            '.toml': 'toml',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp', '.c': 'c', '.h': 'c',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.dart': 'dart'
        }.get(ext, "text")
        
    def _on_text_changed(self, value: str) -> None:
        """Obsługuje zdarzenie zmiany tekstu"""
        if not self.editor or not self.is_valid_text_file:
            return
            
        current_content = value
        is_modified = current_content != self._original_content
        
        # Jeśli stan modyfikacji się zmienił, powiadom
        if is_modified != self.modified:
            self._set_modified(is_modified)
    
    def _set_modified(self, modified: bool) -> None:
        """Ustawia stan modyfikacji i powiadamia obserwatorów"""
        self.modified = modified
        
        # Aktualizuj pasek statusu
        self._update_status_bar()
        
        # Wywołaj zarejestrowane callbacki
        for callback in self._modified_callbacks:
            callback(self.file_path, modified)
        
        # Wyślij wiadomość o zmianie stanu
        self.post_message(self.FileModifiedMessage(self.file_path, modified))
    
    def _update_status_bar(self) -> None:
        """Aktualizuje pasek statusu z informacją o stanie pliku"""
        if not self.status_bar:
            return
            
        modified_indicator = "● [Zmodyfikowany]" if self.modified else ""
        status_text = f"📄 {self.file_path.name} {modified_indicator} | Ctrl+S: Save | F5: Reload"
        self.status_bar.update(status_text)
        
    def save(self) -> bool:
        """Zapisuje zawartość edytora do pliku"""
        if not self.editor or not self.is_valid_text_file:
            return False
            
        try:
            content = self.editor.text
            self.file_path.write_text(content, encoding="utf-8")
            self._original_content = content
            self._set_modified(False)
            
            # Informacja o zapisie
            if self.app:
                self.app.notify(f"Zapisano: {self.file_path.name}")
                
            return True
        except Exception as e:
            if self.app:
                self.app.notify(f"Błąd podczas zapisywania: {e}", severity="error")
            self.log.error(f"Błąd podczas zapisywania pliku {self.file_path}: {e}")
            return False
    
    def reload_from_disk(self) -> bool:
        """Odświeża zawartość z dysku"""
        if not self.is_valid_text_file or not self.editor:
            return False
            
        try:
            content = self.file_path.read_text(encoding="utf-8")
            self._original_content = content
            self.editor.text = content
            self._set_modified(False)
            
            # Informacja o odświeżeniu
            if self.app:
                self.app.notify(f"Odświeżono: {self.file_path.name}")
                
            return True
        except Exception as e:
            if self.app:
                self.app.notify(f"Błąd podczas odświeżania: {e}", severity="error")
            self.log.error(f"Błąd podczas odświeżania pliku {self.file_path}: {e}")
            return False
    
    def is_modified(self) -> bool:
        """Zwraca informację czy zawartość została zmodyfikowana"""
        return self.modified
    
    def watch_modified(self, callback: Callable[[Path, bool], None]) -> None:
        """Rejestruje callback do powiadamiania o zmianach"""
        if callback not in self._modified_callbacks:
            self._modified_callbacks.append(callback)
    
    def unwatch_modified(self, callback: Callable[[Path, bool], None]) -> None:
        """Usuwa callback z listy powiadomień"""
        if callback in self._modified_callbacks:
            self._modified_callbacks.remove(callback)
    
    def focus(self) -> None:
        """Ustawia focus na edytorze"""
        if self.editor and self.is_valid_text_file:
            self.editor.focus()
    
    def action_save(self) -> None:
        """Akcja zapisania pliku (Ctrl+S)"""
        self.save()
    
    def action_reload(self) -> None:
        """Akcja odświeżenia pliku (F5)"""
        self.reload_from_disk()
    
    def get_cursor_position(self) -> tuple[int, int]:
        """Zwraca aktualną pozycję kursora (wiersz, kolumna)"""
        if not self.editor or not self.is_valid_text_file:
            return (0, 0)
            
        try:
            # W zależności od sposobu reprezentacji pozycji kursora
            cursor_pos = getattr(self.editor, "cursor_position", None)
            if cursor_pos:
                return (cursor_pos[0] + 1, cursor_pos[1] + 1)
            else:
                return (1, 1)
        except Exception:
            return (1, 1)
    
    def _on_cursor_moved(self, position: tuple) -> None:
        """Obsługuje zdarzenie ruchu kursora"""
        self.update_cursor_position_in_status()
        
    def update_cursor_position_in_status(self) -> None:
        """Aktualizuje informację o pozycji kursora w pasku statusu"""
        if not self.status_bar or not self.editor:
            return
            
        row, col = self.get_cursor_position()
        modified_indicator = "● [Zmodyfikowany]" if self.modified else ""
        status_text = f"📄 {self.file_path.name} {modified_indicator} | Wiersz: {row}, Kolumna: {col} | Ctrl+S: Save | F5: Reload"
        self.status_bar.update(status_text)