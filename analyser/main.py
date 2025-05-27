from analyser.scanner import scan_app_files

def main():
    print("🚀 Analyser działa!")
    files = scan_app_files()
    for path in files:
        print("📄", path)
