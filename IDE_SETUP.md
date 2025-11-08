# IDE Setup Guide

Anleitung zur Einrichtung deiner IDE für das KI-System Projekt.

## VS Code (empfohlen)

### 1. Extensions installieren

Installiere folgende Extensions:
- **Python** (Microsoft) - Python Support
- **Pylance** (Microsoft) - Schneller Type Checker
- **Python Indent** - Besseres Auto-Indent

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension kevinrose.vsc-python-indent
```

### 2. Virtual Environment erstellen und aktivieren

```bash
# Virtual Environment erstellen
python3 -m venv venv

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Windows
# venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt
```

### 3. VS Code Python Interpreter wählen

1. Drücke `Cmd+Shift+P` (Mac) oder `Ctrl+Shift+P` (Windows/Linux)
2. Tippe: "Python: Select Interpreter"
3. Wähle: `./venv/bin/python`

Alternativ:
- Klicke unten rechts auf die Python-Version
- Wähle das venv aus

### 4. Settings

Die Datei `.vscode/settings.json` wurde bereits erstellt mit:
- ✅ Korrekter Python Interpreter Path
- ✅ Type Checking aktiviert
- ✅ Import-Paths konfiguriert

Falls Probleme auftreten, öffne `.vscode/settings.json` und prüfe:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python"
}
```

### 5. Reload Window

Nach Installation der Extensions und Dependencies:
- `Cmd+Shift+P` → "Developer: Reload Window"

### 6. Probleme beheben

#### "Import loguru could not be resolved"

**Ursache:** VS Code nutzt falschen Python Interpreter

**Lösung:**
```bash
# 1. Prüfe dass venv aktiv ist
which python  # Sollte ./venv/bin/python zeigen

# 2. Loguru ist installiert?
pip list | grep loguru

# 3. Falls nicht installiert:
pip install loguru

# 4. VS Code Interpreter neu wählen
# Cmd+Shift+P → "Python: Select Interpreter"
```

#### "None cannot be assigned to str"

**Ursache:** Type-Checking findet potenzielle None-Werte

**Wurde behoben durch:**
- `Optional[str]` Type-Hints in `platform_factory.py`
- Validierung in `create_collector()`

Falls Fehler weiterhin erscheint:
```json
// In .vscode/settings.json anpassen:
{
    "python.analysis.typeCheckingMode": "off"  // Deaktiviert strenges Type Checking
}
```

---

## PyCharm

### 1. Projekt öffnen

- File → Open → KI-SYSTEM Ordner wählen

### 2. Python Interpreter konfigurieren

1. File → Settings (oder PyCharm → Preferences auf Mac)
2. Project: KI-SYSTEM → Python Interpreter
3. Klicke Zahnrad → Add
4. Wähle "Virtualenv Environment" → "Existing environment"
5. Wähle: `./venv/bin/python`

### 3. Dependencies installieren

PyCharm bietet automatisch an, requirements.txt zu installieren.

Oder manuell:
```bash
# Terminal in PyCharm öffnen (Alt+F12)
pip install -r requirements.txt
```

### 4. Source Root setzen

1. Rechtsklick auf `src/` Ordner
2. Mark Directory as → Sources Root

### 5. Type Checking

PyCharm hat eingebaute Type-Checks:
- Settings → Editor → Inspections
- Python → Type Checker aktivieren

---

## Andere IDEs

### Vim/Neovim mit LSP

```vim
" Installiere python-lsp-server
" pip install python-lsp-server

" In deiner vimrc/init.lua:
" LSP für Python aktivieren
```

### Sublime Text

1. Package Control installieren
2. Installiere: "LSP", "LSP-pyright"
3. Python Interpreter konfigurieren

### Emacs

```elisp
;; use-package für lsp-mode
(use-package lsp-mode
  :hook (python-mode . lsp))

;; lsp-pyright installieren
(use-package lsp-pyright)
```

---

## Allgemeine Tipps

### Virtual Environment immer aktivieren

**Vor dem Arbeiten:**
```bash
source venv/bin/activate  # Linux/Mac
```

**Prüfen ob aktiv:**
```bash
which python
# Output sollte sein: /path/to/KI-SYSTEM/venv/bin/python
```

### Type Stubs für bessere Auto-Completion

```bash
# Optional: Type stubs für libraries installieren
pip install types-requests
pip install types-PyYAML
```

### Git Ignore für IDE Files

`.gitignore` ist bereits konfiguriert für:
- `.vscode/` (teilweise)
- `.idea/` (PyCharm)
- `*.pyc`
- `__pycache__/`
- `venv/`

---

## Fehlerbehebung

### Import Errors trotz korrektem Setup

1. **Restart Language Server:**
   - VS Code: `Cmd+Shift+P` → "Python: Restart Language Server"
   - PyCharm: File → Invalidate Caches / Restart

2. **Python Path prüfen:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```
   Sollte `./src` oder working directory enthalten.

3. **Manually add to PYTHONPATH:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

### Type Checking Errors

Falls zu viele False-Positives:

**VS Code:**
```json
{
    "python.analysis.typeCheckingMode": "basic"  // oder "off"
}
```

**PyCharm:**
- Settings → Editor → Inspections → Python
- Deaktiviere einzelne Checks

### Performance Issues

Bei langsamen IDE:

1. Exclude large directories:
   - `venv/`
   - `data/`
   - `logs/`
   - `models/`

2. VS Code `settings.json`:
```json
{
    "files.watcherExclude": {
        "**/venv/**": true,
        "**/data/**": true,
        "**/logs/**": true
    }
}
```

---

## Testing in IDE

### VS Code

```bash
# Terminal in VS Code
python main.py test
python main.py status
```

### PyCharm

- Run → Edit Configurations
- Add new "Python" configuration
- Script path: `main.py`
- Parameters: `test` (oder `status`, `run`, etc.)

### Debug Mode

**VS Code** - `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "KI-System: Test",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["test"],
            "console": "integratedTerminal"
        }
    ]
}
```

**PyCharm:**
- Klicke auf grünen "Bug" Icon
- Setze Breakpoints in Code
- Debug starten

---

## Zusammenfassung

✅ **Must-Do für alle IDEs:**
1. Virtual Environment erstellen: `python3 -m venv venv`
2. Aktivieren: `source venv/bin/activate`
3. Dependencies: `pip install -r requirements.txt`
4. IDE Interpreter auf `./venv/bin/python` setzen

✅ **Optional aber empfohlen:**
- Type-Checking aktivieren
- Auto-Formatting (black/autopep8)
- Linting (flake8/pylint)

❌ **Häufige Fehler vermeiden:**
- ❌ System Python statt venv Python nutzen
- ❌ Dependencies nicht installiert
- ❌ `src/` nicht als Source Root markiert
- ❌ IDE nicht neu gestartet nach Changes

---

Bei Problemen:
1. Prüfe dass venv aktiv: `which python`
2. Prüfe Dependencies: `pip list`
3. Restart IDE
4. Erstelle Issue auf GitHub
