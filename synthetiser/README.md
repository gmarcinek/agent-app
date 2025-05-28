# Synthetiser - Dokumentacja

**Synthetiser** to warstwa syntezy metadanych w systemie AI agent. Obserwuje katalog `.meta/` z plikami analizy kodu i tworzy skonsolidowaną bazę wiedzy w `knowledge.json`.

## 🚀 Instalacja i Uruchomienie

```bash
# Podstawowe uruchomienie (tryb watch)
poetry run synthetiser

# Z opcjami
poetry run synthetiser --mode build --debug
```

## 📋 Tryby Działania

### `--mode watch` (domyślny)
**Obserwacja w czasie rzeczywistym** - monitoruje zmiany w `.meta/` i automatycznie aktualizuje `knowledge.json`.

```bash
poetry run synthetiser
poetry run synthetiser --mode watch
poetry run synthetiser --mode watch --debug
```

**Co robi:**
- Tworzy **backup** istniejącego `knowledge.json`
- Tworzy **startup snapshot** 
- Obserwuje zmiany w `.meta/` w czasie rzeczywistym
- **Incremental updates** dla pojedynczych plików
- **Batch processing** dla wielu zmian naraz
- **Debouncing** - grupuje zmiany w krótkim czasie

**Kiedy używać:** Podczas rozwoju projektu, gdy chcesz żeby knowledge.json był zawsze aktualny.

---

### `--mode build`
**Jednorazowe zbudowanie** knowledge.json od zera.

```bash
poetry run synthetiser --mode build
poetry run synthetiser --mode build --debug
```

**Co robi:**
- Skanuje wszystkie pliki w `.meta/`
- Buduje kompletny `knowledge.json` od podstaw
- Pokazuje statystyki (liczba plików, symboli, czas budowania)
- **Nie tworzy backup** - tylko build

**Kiedy używać:** Gdy chcesz jednorazowo zbudować knowledge.json bez obserwacji.

---

### `--mode rebuild`
**Inteligentna przebudowa** - buduje tylko jeśli potrzeba.

```bash
poetry run synthetiser --mode rebuild
poetry run synthetiser --mode rebuild --debug
```

**Co robi:**
- Sprawdza czy `knowledge.json` istnieje
- Porównuje timestampy z plikami w `.meta/`
- Przebudowuje **tylko jeśli** pliki są nowsze
- Jeśli knowledge.json nie istnieje - buduje od zera

**Kiedy używać:** W skryptach automatyzacji, CI/CD, jako "ensure knowledge is fresh".

---

### `--mode status`
**Status i diagnostyka** knowledge.json.

```bash
poetry run synthetiser --mode status
poetry run synthetiser --mode status --debug
```

**Co pokazuje:**
- ✅/❌ Czy katalog `.meta/` istnieje
- ✅/❌ Czy `knowledge.json` istnieje  
- 📊 Statystyki: liczba plików, symboli
- 🕐 Kiedy został zbudowany/zaktualizowany
- ⚠️ Czy jest aktualny (porównanie z plikami .meta)

**Kiedy używać:** Debugging, sprawdzenie stanu systemu, troubleshooting.

---

### `--mode restore`
**Przywracanie z backup** - odzyskiwanie po problemach.

```bash
poetry run synthetiser --mode restore
```

**Co robi:**
- Szuka pliku `knowledge.backup.json`
- Przywraca go jako `knowledge.json`
- ✅ Sukces jeśli backup istnieje
- ❌ Błąd jeśli brak backup

**Kiedy używać:** Gdy knowledge.json został uszkodzony, po crash'u, recovery.

---

### `--mode compare`
**Porównanie ze startem** - analiza zmian od uruchomienia.

```bash
poetry run synthetiser --mode compare
```

**Co pokazuje:**
- 📄 **Pliki:** +/- ile plików się zmieniło
- 🏷️ **Symbole:** +/- ile symboli się zmieniło  
- ⏱️ **Runtime:** ile czasu minęło od startup snapshot
- ❌ Błąd jeśli brak startup snapshot

**Kiedy używać:** Monitoring zmian, debugging, analiza aktywności projektu.

## ⚙️ Opcje Globalne

### `--debug`
**Szczegółowe logi** - pokazuje każdy krok przetwarzania.

```bash
poetry run synthetiser --debug
poetry run synthetiser --mode build --debug
```

**Co pokazuje w trybie debug:**
- 🔍 Skanowanie każdego pliku
- ✅/❌ Walidacja plików
- 📄 Wczytywanie JSON
- 🔤 Wykrywanie języka
- 📊 Przypisywanie wag
- 📦 Mapowanie zależności
- 📤 Indeksowanie eksportów
- ⏱️ Czasy wykonania

---

### `--config FILE`
**Niestandardowa konfiguracja** - użyj własnego pliku config.

```bash
poetry run synthetiser --config my_config.json
poetry run synthetiser --mode build --config /path/to/config.json
```

**Domyślna lokalizacja:** `synthetiser/synth_config.json`

**Format konfiguracji:**
```json
{
  "index_weight": 0.2,
  "debug": false,
  "batch_size": 20,
  "debounce_delay": 0.5
}
```

---

### `--wait-timeout SECONDS`
**Timeout oczekiwania** na katalog `.meta/` (tylko dla trybu watch).

```bash
poetry run synthetiser --wait-timeout 60
```

**Domyślnie:** 30 sekund

## 📁 Struktura Plików

```
output/
├── .meta/                    # 📂 Pliki analizy (input)
│   ├── app/
│   │   ├── src/
│   │   │   ├── App.tsx.analysis.json
│   │   │   └── ...
│   │   └── package.json.analysis.json
│   └── ...
└── .synth/                   # 📂 Wyjście synthetiser
    ├── knowledge.json        # 📄 Główna baza wiedzy
    ├── knowledge.backup.json # 💾 Backup poprzedniej wersji
    └── knowledge.startup.json # 📸 Snapshot z uruchomienia

synthetiser/
└── synth_config.json         # ⚙️ Konfiguracja synthetiser
```

## 🧠 Format knowledge.json

```json
{
  "metadata": {
    "built_at": 1748439655.1458187,
    "version": "1.0", 
    "total_files": 13,
    "total_symbols": 5,
    "build_time_seconds": 0.095
  },
  "files": {
    "app\\src\\App.tsx.analysis.json": {
      "meta": { /* oryginalny JSON z analizy */ },
      "weight": 1.0,
      "language": "tsx",
      "extension": ".json", 
      "text": true,
      "processed_at": 1748439572.9307353
    }
  },
  "dependencies": {
    "app\\src\\App.tsx.analysis.json": [
      "react",
      "./components/Clock"
    ]
  },
  "symbols": {
    "App": {
      "file": "app\\src\\App.tsx.analysis.json",
      "type": "export"
    }
  }
}
```

## ⚙️ Konfiguracja

**Plik:** `synthetiser/synth_config.json`

```json
{
  "index_weight": 0.2,        // Waga dla plików index.*
  "debug": false,             // Domyślny tryb debug
  "batch_size": 20,           // Próg dla batch processing  
  "debounce_delay": 0.5       // Opóźnienie debouncing (sekundy)
}
```

### Parametry:

**`index_weight`** (0.0-1.0)
- Waga przypisywana plikom `index.*` (poza głównymi stylami)
- Domyślnie: `0.2` (mniejsza waga niż zwykłe pliki)
- **Wyjątki:** `index.css`, `index.scss` mają wagę 1.0 (główne style)

**`debug`** (true/false)  
- Czy domyślnie włączyć szczegółowe logi
- Domyślnie: `false`

**`batch_size`** (liczba)
- Ile zmian w krótkim czasie triggeruje full rebuild
- Domyślnie: `20`
- Mniej = więcej incremental updates
- Więcej = częściej full rebuild

**`debounce_delay`** (sekundy)
- Ile czekać po ostatniej zmianie przed przetworzeniem
- Domyślnie: `0.5` sekund
- Zapobiega przetwarzaniu każdego save w edytorze osobno

## 🔄 Workflow Examples

### Podstawowy Development Workflow
```bash
# Uruchom obserwację w tle
poetry run synthetiser --mode watch

# Pracuj z kodem - synthetiser automatycznie aktualizuje knowledge
code output/app/src/NewComponent.tsx

# Sprawdź status w innym terminalu  
poetry run synthetiser --mode status
```

### CI/CD Pipeline
```bash
# Sprawdź czy knowledge jest aktualny
poetry run synthetiser --mode status

# Zbuduj jeśli potrzeba
poetry run synthetiser --mode rebuild

# Użyj knowledge.json w dalszych krokach
```

### Debugging i Recovery
```bash
# Sprawdź co się dzieje
poetry run synthetiser --mode status --debug

# Porównaj ze startem
poetry run synthetiser --mode compare  

# Odzyskaj z backup jeśli potrzeba
poetry run synthetiser --mode restore

# Zbuduj od zera
poetry run synthetiser --mode build
```

### Performance Testing
```bash
# Zmierz czas budowania
time poetry run synthetiser --mode build

# Zobacz szczegóły
poetry run synthetiser --mode build --debug
```

## 🚨 Troubleshooting

### Problem: "Katalog .meta nie istnieje"
```bash
# Sprawdź czy analyser działał
ls -la output/

# Uruchom analyser najpierw
poetry run analyser
```

### Problem: "Knowledge.json może być nieaktualny"
```bash
# Przebuduj
poetry run synthetiser --mode rebuild

# Lub wymuś build
poetry run synthetiser --mode build
```

### Problem: "Synthetiser nie widzi zmian"
```bash
# Sprawdź czy watchdog działa
poetry run synthetiser --mode watch --debug

# Sprawdź uprawnienia do katalogu
ls -la output/.meta/
```

### Problem: "Pusty knowledge.json"
```bash
# Debug what's happening
poetry run synthetiser --mode build --debug

# Sprawdź czy pliki w .meta są poprawne
head output/.meta/app/src/App.tsx.analysis.json
```

## 🔧 Integration z Agent

W `main.py` dodaj jako trzeci proces:

```python
synthetiser_cmd = ["poetry", "run", "synthetiser", "--mode", "watch"]
synthetiser_process = start_process(synthetiser_cmd, capture_output=False)
```

Pipeline: `kod → analyser → .meta/ → synthetiser → knowledge.json → agent`

## 📊 Performance

**Typowe czasy:**
- **Build 13 plików:** ~95ms
- **Incremental update:** ~5-10ms per file
- **Memory usage:** ~10-20MB
- **Startup time:** ~2-3s (głównie Poetry)

**Optimization tips:**
- Używaj `--mode watch` zamiast rebuilds
- Zwiększ `batch_size` dla mniejszej częstotliwości full rebuilds
- Zmniejsz `debounce_delay` dla szybszej responsywności

## 🎯 Best Practices

1. **Development:** Zawsze uruchamiaj `--mode watch`
2. **CI/CD:** Używaj `--mode rebuild` 
3. **Debugging:** Dodaj `--debug` do każdego polecenia
4. **Recovery:** Regularnie sprawdzaj `--mode status`
5. **Performance:** Monitor czasy z `--debug`

---

**Synthetiser** - Enterprise-grade knowledge synthesis layer 🧠✨