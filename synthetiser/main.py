#!/usr/bin/env python3
"""
Synthetiser - warstwa syntezy metadanych w knowledge.json

Główny entry point dla synthetiser'a. Obserwuje katalog .meta/ i tworzy
skonsolidowaną bazę wiedzy w knowledge.json dla agenta programującego.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from .config import get_config, reload_config
from .watcher import start_meta_watcher
from .knowledge import KnowledgeBuilder


def setup_cli() -> argparse.ArgumentParser:
    """Konfiguruje CLI argumenty"""
    parser = argparse.ArgumentParser(
        description="Synthetiser - warstwa syntezy metadanych",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  poetry run synthetiser                    # Tryb watch (domyślny)
  poetry run synthetiser --mode build       # Jednorazowe zbudowanie
  poetry run synthetiser --mode status      # Status knowledge.json
  poetry run synthetiser --debug           # Tryb debug
  poetry run synthetiser --config custom.json  # Custom config
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["watch", "build", "status", "rebuild", "restore", "compare"],
        default="watch",
        help="Tryb działania (domyślny: watch)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Włącz szczegółowe logi debug"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Ścieżka do custom pliku konfiguracji"
    )
    
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=30,
        help="Timeout oczekiwania na .meta/ w sekundach (domyślny: 30)"
    )
    
    return parser


def mode_watch(args) -> int:
    """Tryb watch - obserwacja zmian w .meta/"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
        config.debug_info()
    
    print("🚀 Synthetiser - tryb obserwacji")
    print(f"📂 Obserwowany katalog: {config.meta_dir}")
    print(f"🎯 Plik docelowy: {config.knowledge_file}")
    
    # Uruchom watcher
    watcher = start_meta_watcher(callback=on_knowledge_updated)
    
    if not watcher.is_running:
        print("❌ Nie udało się uruchomić watchera")
        return 1
    
    try:
        print("👀 Obserwacja uruchomiona. Naciśnij Ctrl+C aby zatrzymać.")
        watcher.wait_for_completion()
        return 0
    except Exception as e:
        print(f"❌ Błąd w trybie watch: {e}")
        return 1


def mode_build(args) -> int:
    """Tryb build - jednorazowe zbudowanie knowledge.json"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
    
    print("🏗️ Synthetiser - tryb build")
    
    if not config.meta_dir.exists():
        print(f"❌ Katalog .meta nie istnieje: {config.meta_dir}")
        return 1
    
    try:
        builder = KnowledgeBuilder()
        knowledge = builder.build_full_knowledge()
        
        if builder.save_knowledge(knowledge):
            print("✅ Zbudowano knowledge.json")
            
            # Pokaż statystyki
            metadata = knowledge.get("metadata", {})
            print(f"📊 Statystyki:")
            print(f"  📄 Plików: {metadata.get('total_files', 0)}")
            print(f"  🏷️ Symboli: {metadata.get('total_symbols', 0)}")
            print(f"  ⏱️ Czas: {metadata.get('build_time_seconds', 0)}s")
            
            return 0
        else:
            print("❌ Błąd zapisu knowledge.json")
            return 1
            
    except Exception as e:
        print(f"❌ Błąd budowania: {e}")
        return 1


def mode_rebuild(args) -> int:
    """Tryb rebuild - przebudowa jeśli potrzebna"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
    
    print("🔄 Synthetiser - tryb rebuild")
    
    try:
        builder = KnowledgeBuilder()
        knowledge = builder.rebuild_if_needed()
        
        if builder.save_knowledge(knowledge):
            print("✅ Knowledge.json sprawdzony/zaktualizowany")
            return 0
        else:
            print("❌ Błąd zapisu knowledge.json")
            return 1
            
    except Exception as e:
        print(f"❌ Błąd rebuild: {e}")
        return 1


def mode_status(args) -> int:
    """Tryb status - informacje o knowledge.json"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
    
    print("📊 Synthetiser - status")
    print(f"📂 Meta dir: {config.meta_dir}")
    print(f"🎯 Knowledge file: {config.knowledge_file}")
    
    # Sprawdź .meta/
    if config.meta_dir.exists():
        meta_files = list(config.meta_dir.rglob("*.json"))
        print(f"✅ Katalog .meta istnieje ({len(meta_files)} plików JSON)")
    else:
        print("❌ Katalog .meta nie istnieje")
    
    # Sprawdź knowledge.json
    if config.knowledge_file.exists():
        try:
            builder = KnowledgeBuilder()
            knowledge = builder.load_existing_knowledge()
            
            if knowledge:
                metadata = knowledge.get("metadata", {})
                print(f"✅ Knowledge.json istnieje:")
                print(f"  📄 Plików: {metadata.get('total_files', 0)}")
                print(f"  🏷️ Symboli: {metadata.get('total_symbols', 0)}")
                print(f"  🕐 Zbudowano: {metadata.get('built_at', 'nieznane')}")
                print(f"  🔄 Ostatnia aktualizacja: {metadata.get('last_updated', 'brak')}")
                
                # Sprawdź aktualność
                if config.meta_dir.exists():
                    meta_files = list(config.meta_dir.rglob("*.json"))
                    if meta_files:
                        newest_meta = max(f.stat().st_mtime for f in meta_files)
                        knowledge_time = metadata.get('built_at', 0)
                        
                        if newest_meta > knowledge_time:
                            print("⚠️ Knowledge.json może być nieaktualny")
                        else:
                            print("✅ Knowledge.json jest aktualny")
            else:
                print("❌ Nie można wczytać knowledge.json")
                
        except Exception as e:
            print(f"❌ Błąd sprawdzania knowledge.json: {e}")
    else:
        print("❌ Knowledge.json nie istnieje")
    
    return 0


def mode_restore(args) -> int:
    """Tryb restore - przywracanie z backup"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
    
    print("🔄 Synthetiser - tryb restore")
    
    try:
        builder = KnowledgeBuilder()
        success = builder.restore_from_backup()
        
        if success:
            print("✅ Przywrócono knowledge z backup")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"❌ Błąd restore: {e}")
        return 1


def mode_compare(args) -> int:
    """Tryb compare - porównanie ze startup"""
    config = get_config()
    
    if args.debug:
        config.set("debug", True)
    
    print("📊 Synthetiser - porównanie ze startem")
    
    try:
        builder = KnowledgeBuilder()
        comparison = builder.compare_with_startup()
        
        if "error" in comparison:
            print(f"❌ {comparison['error']}")
            return 1
        
        print(f"📈 Zmiany od startu:")
        print(f"  📄 Pliki: {comparison['files_changed']:+d}")
        print(f"  🏷️ Symbole: {comparison['symbols_changed']:+d}")
        print(f"  ⏱️ Runtime: {comparison['runtime_seconds']:.1f}s")
        
        return 0
        
    except Exception as e:
        print(f"❌ Błąd porównania: {e}")
        return 1


def on_knowledge_updated(changed_files: List[str]):
    """
    Callback wywoływany po każdej aktualizacji knowledge
    
    Args:
        changed_files: Lista plików które zostały zmienione
    """
    config = get_config()
    
    if config.get("debug"):
        print(f"🔔 Knowledge zaktualizowany na podstawie {len(changed_files)} plików")
    
    # Tutaj można dodać dodatkową logikę, np.:
    # - Powiadomienia
    # - Webhooks
    # - Metrics
    # - Hot reload dla innych komponentów


def main() -> int:
    """Główna funkcja entry point"""
    parser = setup_cli()
    args = parser.parse_args()
    
    # Załaduj custom config jeśli podany
    if args.config:
        if not args.config.exists():
            print(f"❌ Plik konfiguracji nie istnieje: {args.config}")
            return 1
        
        # Reload config z custom path
        reload_config()
        config = get_config()
        config.config_file = args.config
        config.config = config._load_config()
    
    # Ustaw debug jeśli podany
    if args.debug:
        config = get_config()
        config.set("debug", True)
    
    # Wybierz tryb działania
    mode_handlers = {
        "watch": mode_watch,
        "build": mode_build,
        "rebuild": mode_rebuild,
        "status": mode_status,
        "restore": mode_restore,
        "compare": mode_compare
    }
    
    handler = mode_handlers.get(args.mode)
    if not handler:
        print(f"❌ Nieznany tryb: {args.mode}")
        return 1
    
    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\n⏹️ Przerwano przez użytkownika")
        return 0
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def watch_loop():
    """Kompatybilność wsteczna - stary entry point"""
    print("⚠️ Uwaga: watch_loop() jest deprecated, użyj main()")
    sys.argv = ["synthetiser", "--mode", "watch"]
    return main()


if __name__ == "__main__":
    sys.exit(main())