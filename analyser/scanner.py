import os
import mimetypes
from pathlib import Path
from typing import List, Set
from analyser.constants import (
    TEXT_EXTENSIONS, 
    COMMON_TEXT_FILES, 
    IGNORED_DIRS, 
    IGNORED_FILES, 
    IGNORED_PATTERNS
)

def should_ignore_file(filename: str) -> bool:
    """Sprawdza czy plik powinien być ignorowany"""
    # Sprawdź dokładne nazwy
    if filename in IGNORED_FILES:
        return True
    
    # Sprawdź wzorce (pliki zaczynające się od określonych stringów)
    for pattern in IGNORED_PATTERNS:
        if filename.startswith(pattern):
            return True
    
    # Ignoruj wszystkie pliki zaczynające się od kropki (oprócz już sprawdzonych)
    if filename.startswith('.') and not filename.startswith('..'):
        return True
        
    return False

def is_text_file(filepath: str) -> bool:
    """
    Sprawdza czy plik jest plikiem tekstowym na podstawie:
    1. Rozszerzenia
    2. Nazwy pliku (dla plików bez rozszerzenia)
    3. MIME type (jako ostateczność)
    """
    path = Path(filepath)
    
    # Sprawdź rozszerzenie
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    
    # Sprawdź nazwę pliku bez rozszerzenia
    if path.name in COMMON_TEXT_FILES:
        return True
    
    # Sprawdź MIME type dla plików bez rozszerzenia lub nieznanych
    try:
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type and mime_type.startswith('text/'):
            return True
    except:
        pass
    
    # Dodatkowe sprawdzenie dla plików bez rozszerzenia
    if not path.suffix:
        try:
            # Spróbuj odczytać pierwsze bajty i sprawdź czy to tekst
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                # Sprawdź czy zawiera tylko znaki ASCII/UTF-8
                try:
                    chunk.decode('utf-8')
                    # Sprawdź czy nie zawiera zbyt wielu znaków kontrolnych
                    text_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in [9, 10, 13])
                    if len(chunk) == 0 or text_chars / len(chunk) > 0.7:
                        return True
                except UnicodeDecodeError:
                    pass
        except:
            pass
    
    return False

def scan_text_files(root: str = "output/app", 
                   custom_extensions: Set[str] = None,
                   max_file_size_mb: float = 10) -> List[str]:
    """
    Skanuje katalog w poszukiwaniu plików tekstowych.
    
    Args:
        root: Ścieżka do katalogu głównego
        custom_extensions: Dodatkowe rozszerzenia do uwzględnienia
        max_file_size_mb: Maksymalny rozmiar pliku w MB (0 = bez limitu)
    
    Returns:
        Lista ścieżek do plików tekstowych
    """
    collected = []
    extensions = TEXT_EXTENSIONS.copy()
    
    if custom_extensions:
        extensions.update(custom_extensions)
    
    max_size_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb > 0 else float('inf')

    for dirpath, dirnames, filenames in os.walk(root):
        # NOWE: Sprawdź czy jesteśmy wewnątrz ignorowanego katalogu
        path_parts = Path(dirpath).parts
        if any(ignored_dir in path_parts for ignored_dir in IGNORED_DIRS):
            continue  # Pomiń cały ten katalog i jego zawartość
            
        # Usuń foldery, których nie analizujemy (dla kolejnych poziomów)
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        for file in filenames:
            # NOWE: Sprawdź czy plik jest ignorowany (rozszerzona logika)
            if should_ignore_file(file):
                continue
                
            full_path = os.path.join(dirpath, file)
            
            # Sprawdź rozmiar pliku
            try:
                if os.path.getsize(full_path) > max_size_bytes:
                    continue
            except OSError:
                continue
            
            # Sprawdź czy to plik tekstowy
            if is_text_file(full_path):
                collected.append(full_path)

    return collected

def scan_app_files(root: str = "output/app") -> List[str]:
    """Zachowana dla kompatybilności wstecznej"""
    return scan_text_files(root)

# Przykład użycia z dodatkowymi opcjami
if __name__ == "__main__":
    # Podstawowe użycie
    files = scan_text_files(".")
    print(f"Znaleziono {len(files)} plików tekstowych")
    
    # Z dodatkowymi rozszerzeniami
    custom_files = scan_text_files(".", custom_extensions={".custom", ".special"})
    
    # Z limitem rozmiaru (tylko pliki do 5MB)
    small_files = scan_text_files(".", max_file_size_mb=5)
    
    # Wyświetl pierwsze 10 plików
    for file in files[:10]:
        print(file)