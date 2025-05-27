import asyncio
import os
import argparse
from analyser.entrypoint import start_analyser
from analyser.scanner import scan_app_files
from analyser.analyser import analyze_file

async def analyze_all_files(root_path="output/app"):
    """Analizuje wszystkie istniejące pliki przy starcie"""
    print(f"🔍 Skanowanie plików w {root_path}...")
    files = scan_app_files(root_path)
    print(f"📁 Znaleziono {len(files)} plików do analizy")
    
    for i, file_path in enumerate(files, 1):
        print(f"📄 [{i}/{len(files)}] Analizuję: {file_path}")
        await analyze_file(file_path)
    
    print("✅ Wstępna analiza zakończona")

def main():
    parser = argparse.ArgumentParser(description="Analizator plików tekstowych")
    parser.add_argument("--mode", choices=["scan", "watch", "both"], 
                       default="both", help="Tryb działania")
    parser.add_argument("--path", default="output/app", 
                       help="Ścieżka do analizowanego katalogu")
    
    args = parser.parse_args()

    # Upewniamy się, że katalog istnieje
    if not os.path.exists(args.path):
        print(f"📁 Folder '{args.path}' nie istnieje – tworzę...")
        os.makedirs(args.path, exist_ok=True)
    
    async def run():
        if args.mode in ["scan", "both"]:
            await analyze_all_files(args.path)
        
        if args.mode in ["watch", "both"]:
            print("👀 Uruchamiam watcher...")
            # To musi być w osobnym wątku, bo start_analyser blokuje
            import threading
            watcher_thread = threading.Thread(target=lambda: start_analyser(args.path), daemon=True)
            watcher_thread.start()
            
            # Główny wątek czeka
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("🛑 Zatrzymywanie analizatora...")

    asyncio.run(run())

if __name__ == "__main__":
    main()