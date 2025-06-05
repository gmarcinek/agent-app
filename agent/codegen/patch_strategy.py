import os
import subprocess
import tempfile
from datetime import datetime
from agent.validation.static import analyze_file
from llm import LLMClient, Models

llm = LLMClient(Models.QWEN_CODER_32B)

SUPPORTED_LINT_EXTENSIONS = [".tsx", ".ts", ".js", ".jsx", ".py", ".html"]

def strip_code_fences(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()

def validate_and_patch(prompt: str, filepath: str, extension: str, max_attempts: int = 3) -> tuple[str, dict]:
    """
    Próbuje patch'ować istniejący plik na podstawie prompta używając git apply.
    Zwraca: (kod, raport_walidacji)
    
    Flow:
    1. Generuje git patch przez LLM
    2. Zapisuje patch do output/logs/
    3. Aplikuje przez git apply
    4. Waliduje przez static analysis
    5. Jeśli OK - zostawia zmiany w working dir
    6. Jeśli błąd - cofa przez git apply -R
    """
    cwd = "output/app"
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot patch non-existent file: {filepath}")
    
    # Wczytaj oryginalny kod
    with open(filepath, "r", encoding="utf-8") as f:
        original_code = f.read()
    
    for attempt in range(1, max_attempts + 1):
        print(f"🔧 Patch'uję plik (podejście {attempt})...")
        
        # Generate timestamp for this attempt
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
        
        # Specjalny prompt dla git patch
        patch_prompt = f"""
Plik: {filepath}

Aktualny kod:
```
{original_code}
```

Zadanie: {prompt}

Wygeneruj git patch w standardowym formacie diff. Przykład:

--- a/{filepath}
+++ b/{filepath}
@@ -12,7 +12,7 @@
 export const Component = () => {{
-  const [user, setUser] = useState<OldUser>();
+  const [user, setUser] = useState<NewUser>();
   return <div>{{user.name}}</div>;
 }}

INSTRUKCJE:
- Użyj dokładnej ścieżki: {filepath}
- Pokaż tylko zmiany z kontekstem (3 linie przed/po)
- Zachowaj oryginalne formatowanie i wcięcia
- Zmień tylko to co jest konieczne
- NIE dodawaj komentarzy poza patch

Git patch:
"""

        try:
            raw_patch = llm.chat(patch_prompt)
            git_patch = strip_code_fences(raw_patch)
        except Exception as e:
            print(f"❌ Błąd LLM przy generowaniu patch'a: {e}")
            continue
        
        # Zapisz patch do logów
        patch_filename = f"patch_{os.path.basename(filepath)}_{timestamp}.patch"
        patch_file = f"output/logs/{patch_filename}"
        relative_patch_file = f"../logs/{patch_filename}"
        
        os.makedirs("output/logs", exist_ok=True)
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(git_patch)
        
        print(f"📝 Patch zapisany: {patch_file}")
        
        # Apply patch
        apply_result = subprocess.run(
            ["git", "apply", relative_patch_file], 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        
        if apply_result.returncode != 0:
            print(f"❌ Git apply failed: {apply_result.stderr}")
            continue
        
        print(f"✅ Patch applied successfully")
        
        # Pominięcie walidacji dla niewspieranych rozszerzeń
        if extension.lower() not in SUPPORTED_LINT_EXTENSIONS:
            return read_file_content(filepath), {
                "ok": True,
                "details": f"Patch applied successfully - no static analysis for '{extension}'",
                "patch_file": patch_file
            }
        
        # Walidacja statyczna
        ok, report = analyze_file(filepath)
        
        if ok:
            print(f"✅ Patch validation passed")
            return read_file_content(filepath), {
                "ok": True, 
                "details": f"Patch validation passed: {report}",
                "patch_file": patch_file
            }
        else:
            print(f"⚠️ Patch validation failed:\n{report.strip()}")
            
            # Unapply patch (reverse)
            unapply_result = subprocess.run(
                ["git", "apply", "-R", relative_patch_file], 
                cwd=cwd, 
                capture_output=True, 
                text=True
            )
            
            if unapply_result.returncode != 0:
                print(f"❌ Failed to unapply patch: {unapply_result.stderr}")
                # Fallback - restore from original content
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(original_code)
            else:
                print(f"🔄 Patch unapplied successfully")
    
    # Jeśli wszystkie próby patch'a się nie udały
    return original_code, {
        "ok": False, 
        "details": f"Patch failed after {max_attempts} attempts: {report if 'report' in locals() else 'Unknown error'}",
        "patch_file": patch_file if 'patch_file' in locals() else None
    }

def read_file_content(filepath: str) -> str:
    """Helper function to read file content."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()