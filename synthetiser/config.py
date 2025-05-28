import json
import sys
from pathlib import Path
from typing import Dict, Any

class SynthetiserConfig:
    """Konfiguracja dla synthetiser'a"""
    
    def __init__(self, config_path: Path = None):
        self.root = Path(__file__).resolve().parent.parent  # agent-app/
        self.config_file = config_path or (Path(__file__).parent / "synth_config.json")
        self.output_dir = self.root / "output"
        self.meta_dir = self.output_dir / ".meta"
        self.synth_dir = self.output_dir / ".synth"
        self.knowledge_file = self.synth_dir / "knowledge.json"
        
        # Domyślne wartości
        self.defaults = {
            "index_weight": 0.2,
            "debug": False,
            "batch_size": 20,
            "debounce_delay": 0.5
        }
        
        # Wczytaj konfigurację
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Wczytuje konfigurację z pliku JSON"""
        config = self.defaults.copy()
        
        if self.config_file.exists():
            try:
                with self.config_file.open(encoding="utf-8") as f:
                    user_config = json.load(f)
                    config.update(user_config)
                    if config.get("debug"):
                        print(f"✅ Wczytano konfigurację z: {self.config_file}")
            except Exception as e:
                print(f"⚠️ Błąd wczytywania konfiguracji {self.config_file}: {e}", file=sys.stderr)
                print(f"📝 Używam domyślnych wartości", file=sys.stderr)
        else:
            if config.get("debug"):
                print(f"📝 Plik konfiguracji nie istnieje, używam domyślnych wartości")
        
        return config
    
    def get(self, key: str, default=None):
        """Pobiera wartość z konfiguracji"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Ustawia wartość w konfiguracji (tylko w pamięci)"""
        self.config[key] = value
    
    def save(self):
        """Zapisuje aktualną konfigurację do pliku"""
        try:
            self.synth_dir.mkdir(parents=True, exist_ok=True)
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            print(f"💾 Zapisano konfigurację do: {self.config_file}")
        except Exception as e:
            print(f"❌ Błąd zapisywania konfiguracji: {e}", file=sys.stderr)
    
    def ensure_directories(self):
        """Tworzy wymagane katalogi"""
        self.synth_dir.mkdir(parents=True, exist_ok=True)
        if self.get("debug"):
            print(f"📁 Upewniono się o istnieniu: {self.synth_dir}")
    
    def __str__(self):
        return f"SynthetiserConfig(meta_dir={self.meta_dir}, knowledge_file={self.knowledge_file})"
    
    def debug_info(self):
        """Wyświetla informacje debug o konfiguracji"""
        print("🔧 Konfiguracja Synthetiser:")
        print(f"  📂 Root: {self.root}")
        print(f"  📂 Meta dir: {self.meta_dir}")
        print(f"  📂 Synth dir: {self.synth_dir}")
        print(f"  📄 Knowledge file: {self.knowledge_file}")
        print(f"  ⚙️ Config file: {self.config_file}")
        print(f"  🎛️ Settings:")
        for key, value in self.config.items():
            print(f"    {key}: {value}")


# Singleton instance
_config_instance = None

def get_config() -> SynthetiserConfig:
    """Zwraca singleton instancję konfiguracji"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SynthetiserConfig()
    return _config_instance

def reload_config():
    """Przeładowuje konfigurację (dla hot reload)"""
    global _config_instance
    _config_instance = None
    return get_config()