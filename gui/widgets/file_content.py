from pathlib import Path
from textual.widgets import Static, TextArea
from textual.containers import Vertical, Container
from gui.themes.gruvbox_compatible_theme import gruvbox_transparent_theme

class FileContentView(Vertical):
    """Wyświetlanie zawartości pliku z kolorowaniem składni."""

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
    """

    def __init__(self) -> None:
        super().__init__()
        self.current_file: Path | None = None
        self.editor: TextArea | None = None

    def load_file(self, file_path: Path | str) -> None:
        file_path = Path(file_path)
        self.current_file = file_path
        self.remove_children()

        if not file_path.exists():
            self.mount(Static("❌ File does not exist", classes="message"))
            return

        if file_path.is_dir():
            self.mount(Static(f"📁 {file_path.name} is a directory", classes="message"))
            return

        if not self._is_text_file(file_path):
            size = file_path.stat().st_size
            self.mount(Static(f"📦 Binary file: {file_path.name} ({size:,} bytes)", classes="message"))
            return

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.mount(Static(f"❌ Error reading file:\n{e}", classes="message"))
            return

        lines = content.count("\n") + 1
        header_text = f"📄 {file_path.name} ({lines} lines)"
        self.mount(Container(Static(header_text), classes="file-header"))

        language = self._detect_language(file_path)
        
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
            self.editor.register_theme(gruvbox_transparent_theme)
            self.editor.theme = "gruvbox_transparent"
            self.editor.styles.background = "#3c3836" 

        wrapper = Container(self.editor, classes="editor-wrapper")
        self.mount(wrapper)

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
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                chunk.decode("utf-8")
            return True
        except Exception:
            return False
            
    def _detect_language(self, path: Path) -> str:
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

    def show_placeholder(self) -> None:
        self.remove_children()
        self.mount(Static("📄 Select a file to view its content", classes="message"))