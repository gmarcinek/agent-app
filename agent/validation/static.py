import os
import subprocess

def analyze_tsx_file(path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["eslint", path, "--max-warnings=0"],
            capture_output=True,
            text=True,
            check=False
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, f"Błąd uruchamiania ESLint: {e}")

def analyze_python_file(path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["flake8", path],
            capture_output=True,
            text=True,
            check=False
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, f"Błąd uruchamiania flake8: {e}")

def analyze_html_file(path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["htmlhint", path],
            capture_output=True,
            text=True,
            check=False
        )
        return (result.returncode == 0, result.stdout + result.stderr)
    except Exception as e:
        return (False, f"Błąd uruchamiania htmlhint: {e}")

def analyze_file(path: str) -> tuple[bool, str]:
    ext = os.path.splitext(path)[1].lower()

    if ext in [".tsx", ".ts", ".js", ".jsx"]:
        return analyze_tsx_file(path)
    elif ext == ".py":
        return analyze_python_file(path)
    elif ext == ".html":
        return analyze_html_file(path)

    return True, f"(Pominięto analizę – brak obsługi rozszerzenia: {ext})"
