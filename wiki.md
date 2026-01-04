# Font Selector (CustomTkinter) — Wiki

A simple desktop app that helps you pick **one “keeper” font** by repeatedly showing you **3 random fonts** and having you **eliminate 1** each round until only one remains.

It works on **any folder you select**, scans **all subfolders**, and **auto-saves your progress** so you can close the app and come back later.

---

## What this app does (in plain terms)

- You choose a folder that contains font files.
- The app finds all fonts inside it (including subfolders).
- It shows 3 fonts at a time using your sample text.
- You click the one you want to **eliminate**.
- Repeat until 1 font remains.
- The final font is saved as your selected/kept font.

---

## Supported font types

- `.ttf`
- `.otf`
- `.ttc`
- `.otc`

If a font file can’t be loaded, it will be skipped automatically.

---

## Files the app creates (important)

The app saves two kinds of settings/state:

### 1) App settings (always next to the script)
These are global settings for the app, no matter what folder you select.

- `config.json`  
  Stores your sample text + font size (and basic UI preferences).

✅ This file is always created/used **in the same folder as the script**, even if you run the app from somewhere else.

### 2) Selection progress (saved inside the folder you selected)
These are specific to the folder you’re selecting fonts from.

- `font_selection_state.json`  
  Tracks fonts you’ve eliminated **in realtime** (saved every click).

- `font_selection_selected.txt`  
  Written once the winner is chosen. Contains:
  - the font’s path relative to the selected folder
  - the font’s full absolute path

✅ These files are always stored **inside the selected input folder**, so each folder can have its own separate “tournament”.

---

# Setup / Install (simple to advanced)

## Option A — Fastest (already have Python)

### 1) Install Python
- Recommended: **Python 3.10+**
- If you’re on Windows: make sure **“Add Python to PATH”** is checked during install.

### 2) Put the files in a folder
You should have these files next to each other:

- `font_selector_app.py` (whatever you named the app script)
- `requirements.txt`

### 3) Install dependencies
Open a terminal in that folder and run:

**Windows (PowerShell / CMD)**
```bat
python -m pip install -r requirements.txt
````

**Mac / Linux**

```bash
python3 -m pip install -r requirements.txt
```

### 4) Run the app

**Windows**

```bat
python font_selector_app.py
```

**Mac / Linux**

```bash
python3 font_selector_app.py
```

---

## Option B — Recommended (use a virtual environment)

This keeps installs clean and avoids version conflicts.

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python font_selector_app.py
```

### Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python3 font_selector_app.py
```

---

# Using the app (simple to advanced)

## 1) Select your font folder

Click:

**Select Directory…**

Pick the folder that contains your fonts (or folders of fonts).

The app will automatically:

* scan that folder (including subfolders)
* load progress from `font_selection_state.json` if it already exists

---

## 2) Eliminate fonts until one remains

Each round you’ll see 3 options.

Click the font preview button for the font you want to **eliminate**.

The app will:

* remove it from the “remaining” pool
* save it into `font_selection_state.json` immediately

Repeat until only one font remains.

---

## 3) When you finish

When one font remains, the app shows your final choice and saves:

* `font_selection_state.json` (includes the kept font)
* `font_selection_selected.txt` (easy to read / copy)

You can close the app at that point.

---

# Changing the sample text + size

On the left panel:

* **Sample Text**: what will be displayed in the font previews
* **Font Size (scale)**: how big the text appears in previews

Click:

**Apply Sample Settings**

This updates:

* the preview immediately
* `config.json` next to the script

✅ Your sample settings stay the same the next time you run the app.

---

# Resume where you left off (auto-load)

If you:

* close the app mid-selection
* reopen it later
* select the same directory again

…it will automatically load:

* `font_selection_state.json`

and continue with the fonts that were not eliminated yet.

---

# Resetting a directory’s progress

If you want to start over for the selected directory:

Click:

**Reset State for This Directory**

This will delete:

* `font_selection_state.json`
* `font_selection_selected.txt`

Then it will re-scan the folder and start fresh.

This does **not** affect any other folder you’ve used.

---

# Practical workflow examples

## Example 1 — Picking a font for a logo

1. Put a bunch of fonts in a folder (subfolders ok).
2. Set sample text to your brand name.
3. Set a bigger font size (ex: 80).
4. Run elimination until one remains.
5. Use the selected font path from `font_selection_selected.txt`.

## Example 2 — Different projects use different folders

* Project A fonts in `D:\Fonts\ProjectA`
* Project B fonts in `D:\Fonts\ProjectB`

Each folder will keep its own:

* eliminated list
* final chosen font

---

# Troubleshooting

## “No supported fonts found”

This usually means:

* the folder has no `.ttf/.otf/.ttc/.otc`
* or the fonts are corrupted / not loadable

Try:

* a different folder
* verifying the fonts open in another font viewer

---

## Fonts look clipped or too small

Try:

* increasing **Font Size (scale)**
* shortening sample text
* using a simpler sample text like: `Aa Bb 123`

---

## I changed the folder contents and progress feels “off”

If you add/remove fonts after you started:

* the app still honors eliminated fonts it already recorded
* newly added fonts may show up as candidates

If you want a clean run:

* use **Reset State for This Directory**

---

# FAQ

## Does it scan subfolders?

Yes. It recursively scans the entire selected folder.

## Does it save after every click?

Yes. Eliminations are written to `font_selection_state.json` in realtime.

## Where does `config.json` go?

Always in the same folder as the script file, regardless of where you run it from.

## Where does the selection state go?

Inside the selected input directory.

---

# Requirements

* Python 3.10+ recommended
* Dependencies installed via `requirements.txt`

If you need a packaged `.exe` version later, you can build one (PyInstaller) — but the regular Python version is the simplest way to run it.
