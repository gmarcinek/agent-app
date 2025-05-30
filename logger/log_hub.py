"""
GlobalLogHub - Centralizowany system logowania
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import threading
from collections import deque

from .log_models import LogLevel, LogEntry, ModuleConfig
from .formatters import ConsoleFormatter, LogFormatter


class GlobalLogHub:
    """
    Singleton hub do centralnego zarządzania logami
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.modules: Dict[str, ModuleConfig] = {}
        self.logs: deque[LogEntry] = deque(maxlen=1000)  # Limit do 1000 logów
        self.listeners: List[Callable[[LogEntry], None]] = []
        self.current_level: LogLevel = LogLevel.INFO
        self.group_stack: List[str] = []
        self.formatter: LogFormatter = ConsoleFormatter()
        self._lock = threading.Lock()
        
        # Pre-register common modules
        self._register_default_modules()
    
    def _register_default_modules(self):
        """Zarejestruj domyślne moduły"""
        self.register_module("MANAGER", "⚙️", "blue")
        self.register_module("AGENT", "🤖", "green") 
        self.register_module("SYNTHETISER", "🔧", "yellow")
        self.register_module("GUI", "🖥️", "purple")
    
    @classmethod
    def get_instance(cls) -> 'GlobalLogHub':
        """Pobierz instancję singleton"""
        return cls()
    
    def register_module(self, name: str, icon: str = "📋", color: str = "white") -> None:
        """
        Zarejestruj moduł w hub'ie
        
        Args:
            name: Nazwa modułu (np. "AGENT", "MANAGER")
            icon: Emoji/ikona dla modułu
            color: Kolor logów (dla przyszłego formatowania)
        """
        with self._lock:
            self.modules[name] = ModuleConfig(name, icon, color)
    
    def set_formatter(self, formatter: LogFormatter) -> None:
        """Ustaw formatter dla logów"""
        self.formatter = formatter
    
    def add_listener(self, callback: Callable[[LogEntry], None]) -> None:
        """Dodaj listener do otrzymywania nowych logów"""
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[LogEntry], None]) -> None:
        """Usuń listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def set_log_level(self, level: LogLevel) -> None:
        """Ustaw minimalny poziom logowania"""
        self.current_level = level
    
    def _should_log(self, level: LogLevel) -> bool:
        """Sprawdź czy log powinien być zapisany"""
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARN: 2,
            LogLevel.ERROR: 3
        }
        return level_priority[level] >= level_priority[self.current_level]
    
    def _emit_log(self, level: LogLevel, module: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Wewnętrzna metoda emitowania logu"""
        if not self._should_log(level):
            return
            
        # Sprawdź czy moduł jest zarejestrowany
        if module not in self.modules:
            self.register_module(module, "❓", "gray")
        
        module_config = self.modules[module]
        if not module_config.enabled:
            return
        
        # Twórz wpis
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            module=module,
            message=message,
            icon=module_config.icon,
            color=module_config.color,
            data=data,
            group_id=self.group_stack[-1] if self.group_stack else None,
            group_level=len(self.group_stack)
        )
        
        with self._lock:
            self.logs.append(entry)
        
        # Powiadom listeners
        for listener in self.listeners:
            try:
                listener(entry)
            except Exception as e:
                # Nie loguj błędów w listener'ach żeby uniknąć nieskończonej pętli
                print(f"Error in log listener: {e}")
    
    # Główne metody logowania
    def debug(self, module: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log debug"""
        self._emit_log(LogLevel.DEBUG, module, message, data)
    
    def info(self, module: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log info"""
        self._emit_log(LogLevel.INFO, module, message, data)
    
    def warn(self, module: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning"""
        self._emit_log(LogLevel.WARN, module, message, data)
    
    def error(self, module: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log error"""
        self._emit_log(LogLevel.ERROR, module, message, data)
    
    # Grupowanie logów
    def group_start(self, module: str, operation: str) -> None:
        """Rozpocznij grupę logów"""
        group_id = f"{module}_{len(self.group_stack)}_{datetime.now().timestamp()}"
        self.group_stack.append(group_id)
        self.info(module, f"▶️ {operation}")
    
    def group_end(self, module: str, result: str = "completed") -> None:
        """Zakończ grupę logów"""
        if self.group_stack:
            self.group_stack.pop()
        self.info(module, f"✅ {result}")
    
    # Utility methods
    def get_logs(self, module: Optional[str] = None, level: Optional[LogLevel] = None, limit: int = 100) -> List[LogEntry]:
        """Pobierz logi z filtrami"""
        with self._lock:
            filtered_logs = list(self.logs)
        
        if module:
            filtered_logs = [log for log in filtered_logs if log.module == module]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        return filtered_logs[-limit:]
    
    def clear_logs(self) -> None:
        """Wyczyść wszystkie logi"""
        with self._lock:
            self.logs.clear()
    
    def enable_module(self, module: str, enabled: bool = True) -> None:
        """Włącz/wyłącz logi z modułu"""
        if module in self.modules:
            self.modules[module].enabled = enabled
    
    def format_entry(self, entry: LogEntry) -> str:
        """Formatuj wpis do wyświetlenia"""
        return self.formatter.format_entry(entry)
    
    def get_recent_formatted(self, limit: int = 50) -> List[str]:
        """Pobierz ostatnie logi w formacie tekstowym"""
        recent_logs = self.get_logs(limit=limit)
        return [self.format_entry(entry) for entry in recent_logs]


# Convenience functions dla łatwego użycia
def get_log_hub() -> GlobalLogHub:
    """Shortcut do pobrania hub'a"""
    return GlobalLogHub.get_instance()


def register_module(name: str, icon: str = "📋", color: str = "white") -> None:
    """Shortcut do rejestracji modułu"""
    get_log_hub().register_module(name, icon, color)