"""
Formattery dla różnych typów wyjścia logów
"""
from abc import ABC, abstractmethod
from typing import List
from .log_models import LogEntry


class LogFormatter(ABC):
    """Bazowy formatter logów"""
    
    @abstractmethod
    def format_entry(self, entry: LogEntry) -> str:
        """Formatuj pojedynczy wpis"""
        pass
    
    def format_entries(self, entries: List[LogEntry]) -> List[str]:
        """Formatuj listę wpisów"""
        return [self.format_entry(entry) for entry in entries]


class ConsoleFormatter(LogFormatter):
    """Formatter dla konsoli/terminala"""
    
    def format_entry(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        indent = "  " * entry.group_level
        
        # Podstawowy format
        formatted = f"[{timestamp}] {entry.icon} {entry.module}: {indent}{entry.message}"
        
        # Dodaj dane jeśli istnieją
        if entry.data:
            formatted += f" | {entry.data}"
        
        return formatted


class CompactFormatter(LogFormatter):
    """Kompaktowy formatter dla GUI"""
    
    def format_entry(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        indent = "  " * entry.group_level
        
        # Krótszy format
        return f"[{timestamp}] {entry.icon} {indent}{entry.message}"


class DetailedFormatter(LogFormatter):
    """Szczegółowy formatter z pełnymi informacjami"""
    
    def format_entry(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        indent = "  " * entry.group_level
        
        # Pełny format
        formatted = f"[{timestamp}] [{entry.level.value}] {entry.icon} {entry.module}: {indent}{entry.message}"
        
        # Dodaj dane jeśli istnieją
        if entry.data:
            formatted += f"\n    Data: {entry.data}"
        
        if entry.group_id:
            formatted += f"\n    Group: {entry.group_id}"
        
        return formatted


class JSONFormatter(LogFormatter):
    """Formatter do eksportu JSON"""
    
    def format_entry(self, entry: LogEntry) -> str:
        import json
        
        data = {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level.value,
            "module": entry.module,
            "message": entry.message,
            "icon": entry.icon,
            "color": entry.color,
            "group_level": entry.group_level
        }
        
        if entry.data:
            data["data"] = entry.data
        
        if entry.group_id:
            data["group_id"] = entry.group_id
        
        return json.dumps(data, ensure_ascii=False)