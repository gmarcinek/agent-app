"""
Modele danych dla systemu logowania
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass


class LogLevel(Enum):
    """Poziomy logowania"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """Pojedynczy wpis w logach"""
    timestamp: datetime
    level: LogLevel
    module: str
    message: str
    icon: str
    color: str
    data: Optional[Dict[str, Any]] = None
    group_id: Optional[str] = None
    group_level: int = 0


@dataclass
class ModuleConfig:
    """Konfiguracja modułu"""
    name: str
    icon: str
    color: str
    enabled: bool = True