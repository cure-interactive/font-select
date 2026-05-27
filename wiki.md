# Font Select Wiki

Font Select helps choose one keeper font from a directory. It scans the selected directory recursively, shows three candidate fonts at a time, and saves progress as fonts are eliminated.

## Quick Start

```bash
python setup.py --venv
python font_select.py
```

Manual install:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python font_select.py
```

On Linux or macOS, use `source .venv/bin/activate`.

## Supported Font Files

- `.ttf`
- `.otf`
- `.ttc`
- `.otc`

Fonts that cannot be loaded are skipped.

## App State

Font Select writes:

- `config.json` beside `font_select.py` for global app settings and recent input folders
- `font_selection_state.json` inside the selected font directory for elimination progress
- `font_selection_selected.txt` inside the selected font directory when a winner is chosen

These runtime files are ignored by this repository.

## Workflow

1. Start `font_select.py`.
2. Select a directory containing fonts.
3. Click the preview for the font to eliminate.
4. Continue until one font remains.

Use `input_example/` for a small local test set.
