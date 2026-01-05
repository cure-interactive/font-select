import os
import sys
import json
import random
import datetime
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog

from PIL import ImageFont, ImageTk, ImageDraw, Image


# =============================================================================
# Paths / Helpers
# =============================================================================

def get_script_dir() -> str:
  """
  Return the directory this script is running from.

  Supports:
    - Normal python execution (__file__)
    - Frozen executables (PyInstaller) via sys.frozen
  """
  if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    return os.path.dirname(os.path.abspath(sys.executable))
  return os.path.dirname(os.path.abspath(__file__))


def iso_now() -> str:
  return datetime.datetime.now(datetime.timezone.utc).isoformat()


PATH_DIR_SCRIPT = get_script_dir()

PATH_CONFIG_JSON = os.path.join(PATH_DIR_SCRIPT, "config.json")

STATE_FILENAME = "font_selection_state.json"
SELECTED_FILENAME = "font_selection_selected.txt"


# =============================================================================
# Defaults / Config
# =============================================================================

DEFAULT_CONFIG = {
  "window": {
    "title": "Font Selector",
    "width": 980,
    "height": 820
  },
  "appearance_mode": "System",       # "System", "Dark", "Light"
  "color_theme": "blue",             # "blue", "green", "dark-blue"
  "colors": {
    "blue": "#66aaff",
    "blue_dark": "#334455",
    "red": "#ff4444"
  },
  "sample_text_to_display": "SYNTICORE WEBSITE COMPILER",
  "sample_text_scale": 45,

  "recent_input_dirs_max": 10,
  "recent_input_dirs": []
}


def _read_json(path: str) -> dict | None:
  try:
    if not os.path.exists(path):
      return None
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return None


def _write_json_atomic(path: str, data: dict) -> None:
  """
  Best-effort atomic JSON write:
  - write to temp file then replace
  """
  os.makedirs(os.path.dirname(path), exist_ok=True)
  tmp = path + ".tmp"
  with open(tmp, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  os.replace(tmp, path)


def _norm_dir(p: str) -> str:
  return os.path.normpath(os.path.abspath(p))


def _dedupe_keep_order(items: list[str]) -> list[str]:
  seen = set()
  out: list[str] = []
  for x in items:
    if x in seen:
      continue
    seen.add(x)
    out.append(x)
  return out


def _filter_existing_dirs(items: list[str]) -> list[str]:
  out: list[str] = []
  for p in items:
    try:
      if os.path.isdir(p):
        out.append(p)
    except Exception:
      pass
  return out


def load_or_create_config(path: str) -> dict:
  cfg = _read_json(path)
  if isinstance(cfg, dict):
    # Merge shallowly with defaults (keep unknown user keys too)
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(cfg)
    # Merge nested keys we care about
    if isinstance(cfg.get("window"), dict):
      merged["window"].update(cfg["window"])
    if isinstance(cfg.get("colors"), dict):
      merged["colors"].update(cfg["colors"])
    return merged

  _write_json_atomic(path, DEFAULT_CONFIG)
  return json.loads(json.dumps(DEFAULT_CONFIG))


def clamp_int(value, lo: int, hi: int, fallback: int) -> int:
  try:
    n = int(value)
    return max(lo, min(hi, n))
  except Exception:
    return fallback


# =============================================================================
# Window Icon (title bar / taskbar best-effort)
# =============================================================================

def set_window_icon(root, ico_path: str, png_path: str) -> None:
  """
  Best-effort window icon:
  - Windows: root.iconbitmap(.ico)
  - Linux/macOS: root.iconphoto(.png)
  Keeps a reference to PhotoImage to avoid GC.
  """
  import os
  import tkinter as tk

  ico_abs = os.path.abspath(ico_path) if ico_path else ""
  png_abs = os.path.abspath(png_path) if png_path else ""

  # Windows: .ico
  try:
    if ico_abs and os.path.isfile(ico_abs):
      root.iconbitmap(ico_abs)
  except Exception:
    pass

  # Cross-platform: .png
  try:
    if png_abs and os.path.isfile(png_abs):
      img = tk.PhotoImage(file=png_abs)
      root.iconphoto(True, img)
      root._iconphoto_ref = img  # prevent garbage collection
  except Exception:
    pass


# =============================================================================
# App
# =============================================================================

class FontSelectorApp(ctk.CTk):
  def __init__(self):
    super().__init__()

    self._SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))  # if you don't already have it

    set_window_icon(
      self,
      os.path.join(self._SCRIPT_DIR, "icon.ico"),
      os.path.join(self._SCRIPT_DIR, "icon.png"),
    )

    # Load config.json local to script, regardless of CWD.
    self.config_data = load_or_create_config(PATH_CONFIG_JSON)

    # Recent input directories (local config.json beside script)
    self.recent_input_dirs_max = clamp_int(
      self.config_data.get("recent_input_dirs_max", 10),
      1,
      50,
      10
    )

    recent_raw = self.config_data.get("recent_input_dirs", [])
    if not isinstance(recent_raw, list):
      recent_raw = []

    self.recent_input_dirs: list[str] = []
    for p in recent_raw:
      if isinstance(p, str) and p.strip():
        self.recent_input_dirs.append(_norm_dir(p.strip()))

    self.recent_input_dirs = _dedupe_keep_order(self.recent_input_dirs)
    self.recent_input_dirs = _filter_existing_dirs(self.recent_input_dirs)
    self.recent_input_dirs = self.recent_input_dirs[: self.recent_input_dirs_max]

    # Persist cleaned list
    self.config_data["recent_input_dirs_max"] = self.recent_input_dirs_max
    self.config_data["recent_input_dirs"] = list(self.recent_input_dirs)
    _write_json_atomic(PATH_CONFIG_JSON, self.config_data)

    self.var_recent_dir = tk.StringVar(value=(self.recent_input_dirs[0] if self.recent_input_dirs else "(none)"))

    ctk.set_appearance_mode(self.config_data.get("appearance_mode", "System"))
    ctk.set_default_color_theme(self.config_data.get("color_theme", "blue"))

    self.colors = self.config_data.get("colors", DEFAULT_CONFIG["colors"])
    self.color_blue = self.colors.get("blue", "#66aaff")
    self.color_blue_dark = self.colors.get("blue_dark", "#334455")
    self.color_red = self.colors.get("red", "#ff4444")

    w = self.config_data.get("window", {}).get("width", 980)
    h = self.config_data.get("window", {}).get("height", 820)
    title = self.config_data.get("window", {}).get("title", "Font Selector")

    self.title(title)
    self.geometry(f"{w}x{h}")

    # Runtime state
    self.warn_on_close = True

    self.sample_text_to_display = self.config_data.get("sample_text_to_display", DEFAULT_CONFIG["sample_text_to_display"])
    self.sample_text_scale = clamp_int(self.config_data.get("sample_text_scale", DEFAULT_CONFIG["sample_text_scale"]), 6, 300, 45)

    self.input_dir: str | None = None
    self.path_state_json: str | None = None
    self.path_selected_txt: str | None = None

    self.state_data: dict | None = None
    self.eliminated_set: set[str] = set()

    self.all_fonts: list[tuple[str, str]] = []      # [(rel_label, abs_path), ...] for input_dir
    self.remaining_fonts: list[tuple[str, str]] = []  # filtered against eliminated_set
    self.total_fonts_at_start: int = 0

    self.current_group: list[tuple[str, str]] = []

    self._image_cache: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}

    # UI
    self._build_ui()

    # Closing handler
    self.protocol("WM_DELETE_WINDOW", self.on_closing)

  # -----------------------------------------------------------------------------
  # UI
  # -----------------------------------------------------------------------------

  def _build_ui(self) -> None:
    self.grid_columnconfigure(0, weight=0)
    self.grid_columnconfigure(1, weight=1)
    self.grid_rowconfigure(0, weight=1)

    # Left panel
    self.panel = ctk.CTkFrame(self, corner_radius=12)
    self.panel.grid(row=0, column=0, sticky="nsw", padx=12, pady=12)

    self.panel.grid_columnconfigure(0, weight=1)

    self.lbl_dir_title = ctk.CTkLabel(self.panel, text="Input Directory", font=("Helvetica", 16, "bold"))
    self.lbl_dir_title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

    self.lbl_dir_value = ctk.CTkLabel(self.panel, text="(none selected)", justify="left", wraplength=260)
    self.lbl_dir_value.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

    self.lbl_recent_title = ctk.CTkLabel(self.panel, text="Recent", font=("Helvetica", 14, "bold"))
    self.lbl_recent_title.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))

    self.recent_dir_menu = ctk.CTkOptionMenu(
      self.panel,
      variable=self.var_recent_dir,
      values=(self.recent_input_dirs if self.recent_input_dirs else ["(none)"]),
      command=self._on_recent_dir_selected
    )
    self.recent_dir_menu.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

    self.btn_pick_dir = ctk.CTkButton(
      self.panel,
      text="Select Directory…",
      fg_color=self.color_blue,
      hover_color=self.color_red,
      command=self.select_directory
    )
    self.btn_pick_dir.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))

    # Sample text controls
    self.lbl_sample = ctk.CTkLabel(self.panel, text="Sample Text", font=("Helvetica", 14, "bold"))
    self.lbl_sample.grid(row=5, column=0, sticky="w", padx=12, pady=(8, 4))

    self.var_sample_text = tk.StringVar(value=self.sample_text_to_display)
    self.entry_sample_text = ctk.CTkEntry(self.panel, textvariable=self.var_sample_text)
    self.entry_sample_text.grid(row=6, column=0, sticky="ew", padx=12, pady=(0, 8))

    self.lbl_scale = ctk.CTkLabel(self.panel, text="Font Size (scale)", font=("Helvetica", 14, "bold"))
    self.lbl_scale.grid(row=7, column=0, sticky="w", padx=12, pady=(8, 4))

    self.var_scale = tk.StringVar(value=str(self.sample_text_scale))
    self.entry_scale = ctk.CTkEntry(self.panel, textvariable=self.var_scale)
    self.entry_scale.grid(row=8, column=0, sticky="ew", padx=12, pady=(0, 8))

    self.btn_apply_sample = ctk.CTkButton(
      self.panel,
      text="Apply Sample Settings",
      fg_color=self.color_blue,
      hover_color=self.color_red,
      command=self.apply_sample_settings
    )
    self.btn_apply_sample.grid(row=9, column=0, sticky="ew", padx=12, pady=(0, 12))

    # State controls
    self.lbl_state = ctk.CTkLabel(self.panel, text="Run State", font=("Helvetica", 14, "bold"))
    self.lbl_state.grid(row=10, column=0, sticky="w", padx=12, pady=(10, 4))

    self.btn_reset_state = ctk.CTkButton(
      self.panel,
      text="Reset State for This Directory",
      fg_color=self.color_blue_dark,
      hover_color=self.color_red,
      command=self.reset_state_for_current_dir
    )
    self.btn_reset_state.grid(row=11, column=0, sticky="ew", padx=12, pady=(0, 12))

    self.hint = ctk.CTkLabel(
      self.panel,
      text="Pick a directory with fonts.\nYou eliminate fonts until one remains.\nState auto-saves to JSON in the input folder.",
      justify="left",
      wraplength=260
    )
    self.hint.grid(row=12, column=0, sticky="w", padx=12, pady=(6, 12))

    # Right/main area
    self.main = ctk.CTkFrame(self, corner_radius=12)
    self.main.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
    self.main.grid_columnconfigure(0, weight=1)
    self.main.grid_rowconfigure(1, weight=1)

    # Progress row
    self.progress_frame = ctk.CTkFrame(self.main)
    self.progress_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
    self.progress_frame.grid_columnconfigure(0, weight=1)

    self.elimination_label = ctk.CTkLabel(
      self.progress_frame,
      text="Fonts Eliminated (0 / 0)",
      font=("Helvetica", 14),
      justify="center"
    )
    self.elimination_label.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

    self.progress_bar = ctk.CTkProgressBar(
      self.progress_frame,
      orientation="horizontal",
      width=500,
      fg_color=self.color_blue_dark,
      progress_color=self.color_red
    )
    self.progress_bar.set(0.0)
    self.progress_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    # Display area
    self.display_frame = ctk.CTkScrollableFrame(self.main, corner_radius=12)
    self.display_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    self.display_frame.grid_columnconfigure(0, weight=1)

    self._render_empty_state()
    self._refresh_recent_dir_menu()

  def _render_empty_state(self) -> None:
    for w in self.display_frame.winfo_children():
      w.destroy()

    label = ctk.CTkLabel(
      self.display_frame,
      text="Select a directory to begin.",
      font=("Helvetica", 24, "bold"),
      text_color=self.color_blue
    )
    label.grid(row=0, column=0, sticky="n", padx=12, pady=40)

  # -----------------------------------------------------------------------------
  # Config / Sample Settings
  # -----------------------------------------------------------------------------

  def apply_sample_settings(self) -> None:
    txt = self.var_sample_text.get().strip()
    if not txt:
      messagebox.showerror("Invalid", "Sample text cannot be empty.")
      return

    scale = clamp_int(self.var_scale.get().strip(), 6, 300, self.sample_text_scale)

    self.sample_text_to_display = txt
    self.sample_text_scale = scale

    # Update config.json next to script
    self.config_data["sample_text_to_display"] = self.sample_text_to_display
    self.config_data["sample_text_scale"] = self.sample_text_scale
    _write_json_atomic(PATH_CONFIG_JSON, self.config_data)

    # Clear image cache (scale/text changed)
    self._image_cache.clear()

    # If mid-run, just re-render current screen
    if self.input_dir and self.remaining_fonts:
      self.show_fonts()

  # -----------------------------------------------------------------------------
  # Directory / State
  # -----------------------------------------------------------------------------

  def _save_recent_dirs_config(self) -> None:
    self.config_data["recent_input_dirs_max"] = self.recent_input_dirs_max
    self.config_data["recent_input_dirs"] = list(self.recent_input_dirs[: self.recent_input_dirs_max])
    _write_json_atomic(PATH_CONFIG_JSON, self.config_data)


  def _push_recent_dir(self, input_dir: str) -> None:
    p = _norm_dir(input_dir)
    if not os.path.isdir(p):
      return

    self.recent_input_dirs = [p] + [x for x in self.recent_input_dirs if x != p]
    self.recent_input_dirs = _dedupe_keep_order(self.recent_input_dirs)
    self.recent_input_dirs = _filter_existing_dirs(self.recent_input_dirs)
    self.recent_input_dirs = self.recent_input_dirs[: self.recent_input_dirs_max]

    self._save_recent_dirs_config()
    self._refresh_recent_dir_menu()


  def _refresh_recent_dir_menu(self) -> None:
    values = list(self.recent_input_dirs)
    if not values:
      values = ["(none)"]
      self.var_recent_dir.set("(none)")
      try:
        self.recent_dir_menu.configure(values=values, state="disabled")
      except Exception:
        pass
      return

    if self.var_recent_dir.get() not in values:
      self.var_recent_dir.set(values[0])

    try:
      self.recent_dir_menu.configure(values=values, state="normal")
    except Exception:
      pass


  def _on_recent_dir_selected(self, value: str) -> None:
    v = (value or "").strip()
    if not v or v == "(none)":
      return
    if not os.path.isdir(v):
      # Remove dead entry + refresh
      self.recent_input_dirs = [x for x in self.recent_input_dirs if x != v]
      self._save_recent_dirs_config()
      self._refresh_recent_dir_menu()
      messagebox.showerror("Recent Directory Missing", f"This directory no longer exists:\n{v}")
      return

    self.load_input_directory(v)

  def select_directory(self) -> None:
    chosen = filedialog.askdirectory(title="Select Font Input Directory")
    if not chosen:
      return
    self.load_input_directory(chosen)

  def load_input_directory(self, input_dir: str) -> None:
    self.input_dir = os.path.abspath(input_dir)
    self._push_recent_dir(self.input_dir)
    self.var_recent_dir.set(self.input_dir)
    self.path_state_json = os.path.join(self.input_dir, STATE_FILENAME)
    self.path_selected_txt = os.path.join(self.input_dir, SELECTED_FILENAME)

    self.lbl_dir_value.configure(text=self.input_dir)

    # Load state from input dir if exists
    self.state_data = self._load_or_init_state(self.input_dir, self.path_state_json)
    self.eliminated_set = set(self.state_data.get("eliminated_fonts", []))

    # Scan fonts (any depth)
    self.all_fonts = self._scan_fonts_recursive(self.input_dir)

    # Determine total-at-start for progress math
    self.total_fonts_at_start = int(self.state_data.get("total_fonts_at_start") or 0)
    if self.total_fonts_at_start <= 0:
      self.total_fonts_at_start = len(self.all_fonts)
      self.state_data["total_fonts_at_start"] = self.total_fonts_at_start
      self._save_state()

    # Filter remaining against eliminated
    self.remaining_fonts = [fp for fp in self.all_fonts if fp[0] not in self.eliminated_set]

    # If eliminated list includes fonts that no longer exist, keep them in JSON
    # (so the run remains consistent historically), but compute remaining based on actual scan.

    # If only 0 fonts found
    if len(self.all_fonts) == 0:
      self._set_progress(eliminated_count=len(self.eliminated_set), total_at_start=max(1, self.total_fonts_at_start))
      self._render_message("No supported fonts found in this directory.\n(Scanning: .ttf .otf .ttc .otc)")
      return

    # If run already finished previously, show final if we have it
    kept = self.state_data.get("kept_font")
    if kept and isinstance(kept, dict) and kept.get("path_rel"):
      # Still show final screen; user can reset if they want.
      kept_rel = kept.get("path_rel")
      kept_abs = os.path.join(self.input_dir, kept_rel) if kept_rel else None
      if kept_abs and os.path.exists(kept_abs):
        self._show_final_choice(kept_rel, kept_abs, already_saved=True)
        return

    # If only one remaining, that is the kept font
    if len(self.remaining_fonts) == 1:
      rel, abs_path = self.remaining_fonts[0]
      self._finalize_kept_font(rel, abs_path)
      return

    # Start or resume
    self.create_new_group()
    self.show_fonts()

  def _load_or_init_state(self, input_dir: str, state_path: str) -> dict:
    data = _read_json(state_path)
    if isinstance(data, dict) and int(data.get("schema_version", 0)) == 1:
      return data

    # New state
    return {
      "schema_version": 1,
      "input_dir": input_dir,
      "created_at": iso_now(),
      "updated_at": iso_now(),
      "sample_text_to_display_at_start": self.sample_text_to_display,
      "sample_text_scale_at_start": self.sample_text_scale,
      "total_fonts_at_start": 0,
      "eliminated_fonts": [],
      "kept_font": None
    }

  def _save_state(self) -> None:
    if not self.path_state_json or not self.state_data:
      return
    self.state_data["updated_at"] = iso_now()
    _write_json_atomic(self.path_state_json, self.state_data)

  def reset_state_for_current_dir(self) -> None:
    if not self.input_dir or not self.path_state_json:
      messagebox.showinfo("Reset", "Select a directory first.")
      return

    if not messagebox.askokcancel(
      "Reset state",
      "This will clear eliminated fonts + final selection for the currently selected directory.\n\nProceed?"
    ):
      return

    # Delete state files if they exist
    try:
      if os.path.exists(self.path_state_json):
        os.remove(self.path_state_json)
    except Exception:
      pass

    try:
      if self.path_selected_txt and os.path.exists(self.path_selected_txt):
        os.remove(self.path_selected_txt)
    except Exception:
      pass

    # Reload directory fresh
    self._image_cache.clear()
    self.load_input_directory(self.input_dir)

  # -----------------------------------------------------------------------------
  # Font scanning / rendering
  # -----------------------------------------------------------------------------

  def _scan_fonts_recursive(self, root_dir: str) -> list[tuple[str, str]]:
    supported: list[tuple[str, str]] = []

    for root, _dirs, files in os.walk(root_dir):
      for name in files:
        ext = os.path.splitext(name)[1].lower()
        if ext not in (".ttf", ".otf", ".ttc", ".otc"):
          continue

        abs_path = os.path.join(root, name)
        rel_label = os.path.relpath(abs_path, root_dir)

        try:
          # Validate font is loadable
          ImageFont.truetype(abs_path)
          supported.append((rel_label, abs_path))
        except Exception:
          # Skip unsupported
          continue

    # Stable ordering helps state consistency if you ever change randomness seed logic later
    supported.sort(key=lambda x: x[0].lower())
    return supported

  def _create_image_with_font(self, font_abs_path: str, text: str, size: int) -> ImageTk.PhotoImage:
    key = (font_abs_path, text, size)
    cached = self._image_cache.get(key)
    if cached:
      return cached

    font = ImageFont.truetype(font_abs_path, size)

    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = max(1, bbox[2] - bbox[0])
    text_h = max(1, bbox[3] - bbox[1])

    padding_x = 22
    padding_y = 18

    img_w = text_w + padding_x * 2
    img_h = text_h + padding_y * 2

    img = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((padding_x, padding_y), text, font=font, fill=(0, 0, 0))

    photo = ImageTk.PhotoImage(img)
    self._image_cache[key] = photo
    return photo

  # -----------------------------------------------------------------------------
  # Game loop logic (eliminate until one remains)
  # -----------------------------------------------------------------------------

  def create_new_group(self) -> None:
    if len(self.remaining_fonts) <= 3:
      self.current_group = self.remaining_fonts[:]
    else:
      self.current_group = random.sample(self.remaining_fonts, 3)

  def show_fonts(self) -> None:
    # If run reached 1 remaining, finalize
    if len(self.remaining_fonts) == 1:
      rel, abs_path = self.remaining_fonts[0]
      self._finalize_kept_font(rel, abs_path)
      return

    for w in self.display_frame.winfo_children():
      w.destroy()

    # Instruction
    row = 0
    instruction = ctk.CTkLabel(
      self.display_frame,
      text="Select a Font to Eliminate",
      font=("Helvetica", 24, "bold"),
      text_color=self.color_red
    )
    instruction.grid(row=row, column=0, sticky="ew", padx=12, pady=(18, 18))
    row += 1

    # Render each font option
    for rel_label, abs_path in self.current_group:
      file_label = ctk.CTkLabel(self.display_frame, text=rel_label, justify="left", wraplength=740)
      file_label.grid(row=row, column=0, sticky="ew", padx=12, pady=(6, 6))
      row += 1

      img = self._create_image_with_font(abs_path, self.sample_text_to_display, self.sample_text_scale)

      btn = ctk.CTkButton(
        self.display_frame,
        text="",
        image=img,
        fg_color=self.color_blue,
        hover_color=self.color_red,
        command=lambda r=rel_label, p=abs_path: self.eliminate_font(r, p)
      )
      # Make the button size follow the image (no hardcoded width)
      btn.configure(width=max(120, img.width()), height=max(44, img.height()))
      btn.grid(row=row, column=0, sticky="n", padx=12, pady=(0, 18))
      row += 1

    # Progress update
    eliminated_count = len(self.eliminated_set)
    self._set_progress(eliminated_count, self.total_fonts_at_start)

  def eliminate_font(self, rel_label: str, abs_path: str) -> None:
    # Remove from remaining
    self.remaining_fonts = [f for f in self.remaining_fonts if f[0] != rel_label]

    # Track elimination
    self.eliminated_set.add(rel_label)
    if self.state_data is not None:
      eliminated_list = self.state_data.get("eliminated_fonts")
      if not isinstance(eliminated_list, list):
        eliminated_list = []
        self.state_data["eliminated_fonts"] = eliminated_list
      if rel_label not in eliminated_list:
        eliminated_list.append(rel_label)

      # Realtime persistence
      self._save_state()

    # If one remains -> keep it
    if len(self.remaining_fonts) == 1:
      rel, abs_keep = self.remaining_fonts[0]
      self._finalize_kept_font(rel, abs_keep)
      return

    # If none remain (shouldn't happen now, but guard)
    if len(self.remaining_fonts) == 0:
      self._render_message("No fonts remaining.\nReset state or select another directory.")
      return

    # Continue
    self.create_new_group()
    self.show_fonts()

  def _finalize_kept_font(self, rel_label: str, abs_path: str) -> None:
    # Set progress to complete: eliminated should be total-1
    self._set_progress(eliminated_count=max(0, self.total_fonts_at_start - 1), total_at_start=self.total_fonts_at_start)

    # Save final selection to txt in input dir
    try:
      if self.path_selected_txt:
        with open(self.path_selected_txt, "w", encoding="utf-8") as f:
          f.write(rel_label + "\n")
          f.write(abs_path + "\n")
    except Exception:
      pass

    # Save final selection into JSON
    if self.state_data is not None:
      self.state_data["kept_font"] = {
        "path_rel": rel_label,
        "path_abs": abs_path
      }
      self._save_state()

    # Show final screen
    self._show_final_choice(rel_label, abs_path, already_saved=False)

  def _show_final_choice(self, rel_label: str, abs_path: str, already_saved: bool) -> None:
    for w in self.display_frame.winfo_children():
      w.destroy()

    self.warn_on_close = False

    title = ctk.CTkLabel(
      self.display_frame,
      text="Font Chosen to Keep",
      font=("Helvetica", 24, "bold"),
      text_color=self.color_blue
    )
    title.grid(row=0, column=0, sticky="ew", padx=12, pady=(18, 14))

    # Preview
    img = self._create_image_with_font(abs_path, self.sample_text_to_display, self.sample_text_scale)
    preview = ctk.CTkLabel(self.display_frame, image=img, text="")
    preview.image = img
    preview.grid(row=1, column=0, sticky="n", padx=12, pady=(0, 16))

    # Message
    extra = ""
    if already_saved:
      extra = "\n\n(Loaded from existing state in this directory.)"

    msg = ctk.CTkLabel(
      self.display_frame,
      text=f"{rel_label}\n\nSaved:\n- {STATE_FILENAME}\n- {SELECTED_FILENAME}{extra}\n\nYou may now close this window.",
      justify="center",
      font=("Helvetica", 18, "bold"),
      text_color=self.color_blue
    )
    msg.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 22))

  # -----------------------------------------------------------------------------
  # Progress helpers
  # -----------------------------------------------------------------------------

  def _set_progress(self, eliminated_count: int, total_at_start: int) -> None:
    # Total eliminations required to pick one kept font = total-1
    denom = max(1, total_at_start - 1)
    eliminated_clamped = max(0, min(eliminated_count, denom))

    self.elimination_label.configure(text=f"Fonts Eliminated ({eliminated_clamped} / {denom})")
    self.progress_bar.set(eliminated_clamped / denom)

  def _render_message(self, text: str) -> None:
    for w in self.display_frame.winfo_children():
      w.destroy()
    label = ctk.CTkLabel(
      self.display_frame,
      text=text,
      font=("Helvetica", 20, "bold"),
      text_color=self.color_red,
      justify="center"
    )
    label.grid(row=0, column=0, sticky="n", padx=12, pady=40)

  # -----------------------------------------------------------------------------
  # Close behavior
  # -----------------------------------------------------------------------------

  def on_closing(self) -> None:
    if not self.warn_on_close:
      self.destroy()
      return

    if messagebox.askokcancel("Quit", "Font selection is still in progress.\nAre you sure you want to quit?"):
      self.destroy()


def main() -> None:
  app = FontSelectorApp()
  app.mainloop()


if __name__ == "__main__":
  main()
