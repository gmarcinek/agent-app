# ProcessManager - Dokumentacja

## Przegląd

ProcessManager to singleton odpowiedzialny za zarządzanie procesami Poetry w systemie. Klasa została zaprojektowana w architekturze "lean" - fokusuje się tylko na zarządzaniu procesami, delegując cleanup do wyspecjalizowanej klasy `ProcessCleaner`.

## Architektura

- **Singleton Pattern** - jedna instancja na aplikację
- **Delegacja cleanup** - wykorzystuje `ProcessCleaner` do bezpiecznego zamykania procesów
- **Thread-safe output reading** - każdy proces ma dedykowany wątek do czytania logów
- **Integracja z GlobalLogHub** - wszystkie logi przechodzą przez centralny system logowania

## Inicjalizacja

```python
from process_manager import ProcessManager

# Automatyczne utworzenie singletona
manager = ProcessManager()
```

### Wbudowane komendy Poetry

```python
poetry_commands = {
    "agent": ["poetry", "run", "agent"],
    "analyser": ["poetry", "run", "analyser-watch", "--mode", "watch"],
    "synthetiser": ["poetry", "run", "synthetiser", "--mode", "watch"]
}
```

## Podstawowe operacje

### Uruchamianie procesów

#### Wszystkie procesy naraz

```python
manager.start_all()
```

#### Pojedynczy proces Poetry

```python
success = manager.start_poetry_process(
    name="agent",
    cmd=["poetry", "run", "agent"],
    working_dir="."  # opcjonalne
)
```

#### Niestandardowy proces

```python
success = manager.start_custom_process(
    name="dev_server",
    cmd=["npm", "start"],
    working_dir="./frontend",
    detached=True,  # bez logowania output
    shell=False
)
```

### Zatrzymywanie procesów

#### Graceful shutdown pojedynczego procesu

```python
success = manager.stop_process("agent")
```

#### Graceful shutdown wszystkich procesów

```python
manager.stop_all()
```

#### Emergency stop (force kill)

```python
manager.emergency_stop_all()
```

### Restart procesu

```python
success = manager.restart_process("agent")
```

## Komunikacja z procesami

### Wysyłanie promptów do agenta

```python
success = manager.send_to_agent("Analyze the latest data")
```

## Monitoring i status

### Sprawdzanie statusu

```python
# Lista uruchomionych procesów
running = manager.get_running_processes()  # ['agent', 'analyser']

# Status konkretnego procesu
is_running = manager.is_running("agent")  # True/False

# Status wszystkich procesów dla UI
status = manager.get_status()
# {'agent': 'running', 'analyser': 'stopped', 'synthetiser': 'running'}
```

### Szczegółowe informacje

#### Info o konkretnym procesie

```python
info = manager.get_process_info("agent")
# {
#     "name": "agent",
#     "pid": 12345,
#     "running": True,
#     "exit_code": None,
#     "thread_alive": True,
#     "command": ["poetry", "run", "agent"]
# }
```

#### Pełny status systemu

```python
system_status = manager.get_system_status()
# {
#     "manager_running": True,
#     "total_processes": 3,
#     "active_processes": 2,
#     "active_threads": 2,
#     "total_system_threads": 8,
#     "processes": { ... }
# }
```

## Zaawansowane funkcje

### Niestandardowe procesy z opcjami

```python
# Windows - nowa grupa procesów
manager.start_custom_process(
    name="windows_service",
    cmd=["service.exe"],
    creation_flags=subprocess.CREATE_NEW_PROCESS_GROUP
)

# Unix - nowa sesja
import os
manager.start_custom_process(
    name="daemon",
    cmd=["./daemon.sh"],
    preexec_fn=os.setsid
)

# Proces w tle bez logów
manager.start_custom_process(
    name="background_task",
    cmd=["long_running_task"],
    detached=True
)
```

## Obsługa błędów

### Kody zwracane

- `True` - operacja zakończona sukcesem
- `False` - operacja zakończona błędem

### Logowanie błędów

Wszystkie błędy są automatycznie logowane przez GlobalLogHub z odpowiednimi poziomami:

- **INFO** - normalne operacje
- **WARN** - ostrzeżenia (proces już uruchomiony, itp.)
- **ERROR** - błędy krytyczne

## Integracja z ProcessCleaner

ProcessManager automatycznie wykorzystuje ProcessCleaner do:

- Graceful shutdown procesów (SIGTERM → SIGKILL)
- Cleanup zombie procesów
- Raportowanie błędów cleanup
- Emergency kill z timeout

## Threading

### Wątki output readers

Każdy uruchomiony proces (nie-detached) ma dedykowany daemon thread do czytania stdout/stderr.

### Thread cleanup

- Wątki są automatycznie czyszczone po zakończeniu procesu
- Emergency stop czyści wszystkie wątki force
- Thread join z timeout podczas graceful shutdown

## Encoding i I/O

### Automatyczne ustawienia encoding

```python
env = {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
    **os.environ
}
```

### Output handling

- UTF-8 encoding z `errors='replace'`
- Line-buffered output (`bufsize=1`)
- Przekazywanie logów do GlobalLogHub w czasie rzeczywistym

## Przykłady użycia

### Typowy workflow

```python
manager = ProcessManager()

# Start całego systemu
manager.start_all()

# Sprawdź status
if manager.is_running("agent"):
    # Wyślij zadanie
    manager.send_to_agent("Process new documents")

# Restart problematycznego procesu
if not manager.is_running("analyser"):
    manager.restart_process("analyser")

# Graceful shutdown na koniec
manager.stop_all()
```

### Monitoring w pętli

```python
import time

while True:
    status = manager.get_status()
    for name, state in status.items():
        if state == "stopped":
            print(f"Process {name} needs restart")
            manager.restart_process(name)

    time.sleep(30)
```

## Ograniczenia

- **Singleton** - tylko jedna instancja ProcessManager na aplikację
- **Poetry processes** - wbudowane komendy są skonfigurowane dla Poetry
- **UTF-8 encoding** - wszystkie procesy uruchamiane z wymuszonym UTF-8
- **Daemon threads** - output readers nie blokują zamykania aplikacji
