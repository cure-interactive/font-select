# Font Select

Desktop app for choosing one keeper font from a folder by repeatedly eliminating fonts from random groups.

## Requirements

- Python 3.10+
- Dependencies from `requirements.txt`

## Install

```bash
python setup.py --venv
```

Or manually:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On Linux or macOS, activate the virtual environment with `source .venv/bin/activate`.

## Run

```bash
python font_select.py
```

## Files

- `font_select.py`: main app
- `input_example/`: sample fonts for trying the app
- `requirements.txt`: runtime dependencies
- `wiki.md`: usage details

The app writes global runtime settings to `config.json` beside the script and selection progress into the chosen font folder.
