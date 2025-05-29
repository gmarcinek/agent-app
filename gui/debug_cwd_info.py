#!/usr/bin/env python3
"""
Debug script - sprawdź gdzie aplikacja się uruchamia
"""

import os
from pathlib import Path

def debug_paths():
    print("=== DEBUG PATHS ===")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Script location: {Path(__file__).parent}")
    print(f"Script parent: {Path(__file__).parent.parent}")
    
    # Sprawdź możliwe lokalizacje output/
    possible_output_dirs = [
        Path("output"),
        Path.cwd() / "output", 
        Path(__file__).parent / "output",
        Path(__file__).parent.parent / "output",
    ]
    
    print("\n=== CHECKING OUTPUT DIRECTORIES ===")
    for i, path in enumerate(possible_output_dirs):
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        print(f"{i+1}. {path}")
        print(f"   Exists: {exists}, Is directory: {is_dir}")
        
        if exists and is_dir:
            try:
                contents = list(path.iterdir())[:5]
                print(f"   Contents (first 5): {[item.name for item in contents]}")
            except Exception as e:
                print(f"   Error listing: {e}")
        print()
    
    # Sprawdź zawartość CWD
    print("=== CURRENT DIRECTORY CONTENTS ===")
    try:
        cwd_contents = list(Path.cwd().iterdir())
        print(f"CWD contents: {[item.name for item in cwd_contents]}")
        
        # Sprawdź czy są foldery które mogą zawierać kod
        code_folders = []
        for item in cwd_contents:
            if item.is_dir() and item.name in ['src', 'app', 'gui', 'output', 'project']:
                code_folders.append(item.name)
        
        print(f"Potential code folders: {code_folders}")
        
    except Exception as e:
        print(f"Error listing CWD: {e}")

if __name__ == "__main__":
    debug_paths()