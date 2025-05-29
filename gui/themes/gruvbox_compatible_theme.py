from textual.widgets.text_area import TextAreaTheme
from rich.style import Style

# Tworzenie theme z przezroczystym tłem dla Textual 3.x
gruvbox_transparent_theme = TextAreaTheme(name="gruvbox_transparent")

# Kluczowe ustawienie przezroczystego tła
gruvbox_transparent_theme.background = "#3c3836"
gruvbox_transparent_theme.foreground = "#ebdbb2"

# Stylizacja kursora
gruvbox_transparent_theme.cursor_style = Style(color="black", bgcolor="#fabd2f")
gruvbox_transparent_theme.cursor_line_style = Style(bgcolor="#45413d")

# Stylizacja guttera (numerów linii)
gruvbox_transparent_theme.gutter_style = Style(color="#928374")

# Zaznaczenie tekstu
gruvbox_transparent_theme.selection_background = "#504945"

# Podświetlanie nawiasów
gruvbox_transparent_theme.bracket_matching_style = Style(bgcolor="#689d6a")

# Scrollbar
gruvbox_transparent_theme.scrollbar_background = "#3c3836"
gruvbox_transparent_theme.scrollbar_handle = "#7c6f64"

# Kompletne style składni
gruvbox_transparent_theme.syntax_styles = {
    # Komentarze
    "comment": Style(color="#928374", italic=True),
    "comment.line": Style(color="#928374", italic=True),
    "comment.block": Style(color="#928374", italic=True),
    
    # Stałe i literały
    "constant": Style(color="#d3869b"),
    "constant.numeric": Style(color="#d79921"),
    "constant.character": Style(color="#d3869b"),
    "constant.language": Style(color="#d3869b", bold=True),
    
    # Słowa kluczowe
    "keyword": Style(color="#fb4934", bold=True),
    "keyword.control": Style(color="#fb4934", bold=True),
    "keyword.operator": Style(color="#fe8019"),
    "keyword.other": Style(color="#fb4934"),
    
    # Stringi
    "string": Style(color="#b8bb26"),
    "string.quoted": Style(color="#b8bb26"),
    "string.interpolated": Style(color="#b8bb26"),
    "string.regexp": Style(color="#8ec07c"),
    
    # Funkcje i metody
    "entity.name.function": Style(color="#8ec07c", bold=True),
    "entity.name.method": Style(color="#8ec07c"),
    "entity.name.class": Style(color="#fabd2f", bold=True),
    "entity.name.type": Style(color="#d3869b"),
    "entity.name.tag": Style(color="#fb4934"),
    
    # Zmienne i identyfikatory
    "variable": Style(color="#ebdbb2"),
    "variable.parameter": Style(color="#ebdbb2"),
    "variable.other": Style(color="#ebdbb2"),
    
    # Typy danych
    "storage.type": Style(color="#fe8019"),
    "storage.modifier": Style(color="#fe8019"),
    
    # Wsparcie (built-ins)
    "support.function": Style(color="#83a598"),
    "support.class": Style(color="#83a598"),
    "support.type": Style(color="#d3869b"),
    
    # Operatory
    "operator": Style(color="#fe8019"),
    "operator.arithmetic": Style(color="#fe8019"),
    "operator.logical": Style(color="#fe8019"),
    "operator.comparison": Style(color="#fe8019"),
    
    # Atrybuty i właściwości
    "entity.other.attribute-name": Style(color="#fabd2f"),
    "meta.attribute": Style(color="#fabd2f"),
    
    # Liczby
    "constant.numeric": Style(color="#d79921"),
    "constant.numeric.integer": Style(color="#d79921"),
    "constant.numeric.float": Style(color="#d79921"),
    
    # Wartości logiczne
    "constant.language.boolean": Style(color="#d3869b"),
    
    # Znaki interpunkcyjne
    "punctuation": Style(color="#ebdbb2"),
    "punctuation.separator": Style(color="#ebdbb2"),
    "punctuation.terminator": Style(color="#ebdbb2"),
    "punctuation.bracket": Style(color="#ebdbb2"),
    
    # Błędy i nieprawidłowe elementy
    "invalid": Style(bgcolor="#cc241d", color="#fbf1c7"),
    "invalid.illegal": Style(bgcolor="#cc241d", color="#fbf1c7", underline=True),
    "invalid.deprecated": Style(color="#fb4934", dim=True),
}