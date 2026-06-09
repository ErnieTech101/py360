"""
terminal.py - PY360 Tkinter Terminal Display Engine
Part of the Python Mainframe Experience Layer

Replaces curses entirely. Provides a fixed 80x24 character grid
in a borderless tkinter window styled as a 3270 Model 2 terminal.

Usage:
    from terminal import Terminal
    term = Terminal()
    term.put(row, col, "Hello World")
    term.refresh()
    term.mainloop()
"""

import tkinter as tk
import tkinter.font as tkfont
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Terminal Constants ---
COLS        = 80
ROWS        = 24
OIA_ROW     = ROWS        # OIA status line is row 24 (0-indexed below data)
TOTAL_ROWS  = ROWS + 1    # 24 data rows + 1 OIA row

# --- Colors ---
COLOR_BG        = "#000000"
COLOR_FG        = "#00FF17"
COLOR_FG_DIM    = "#007A0B"
COLOR_FG_BOLD   = "#80FF80"
COLOR_REVERSE_BG = "#00FF17"
COLOR_REVERSE_FG = "#000000"
COLOR_BORDER    = "#005500"
COLOR_OIA_BG    = "#001A00"
COLOR_OIA_FG    = "#00FF17"

# --- Font ---
FONT_FAMILY = "Courier New"
FONT_SIZE   = 14

# --- Cell attributes ---
ATTR_NORMAL  = 0
ATTR_BOLD    = 1
ATTR_DIM     = 2
ATTR_REVERSE = 3


class Terminal:
    """
    PY360 3270-style terminal built on tkinter.
    Provides a simple character grid API for all PY360 modules.
    """

    def __init__(self, sysname: str = "PY360", userid: str = ""):
        self.sysname  = sysname
        self.userid   = userid
        self._text_ids  = {}     # built in _build_grid
        self._cells     = {}     # (row, col) -> (char, attr)
        self._cursor    = (0, 0)
        self._insert    = False
        self._running   = True
        self._keyqueue  = []
        self._key_callback = None
        self._oia_tick_id  = None

        self._build_window()
        self._build_grid()
        self._draw_bezel()
        self._render_oia()
        self._tick_oia()

    # --- Window Construction ---

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("PY360 - Mainframe Simulator")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # Use Windows API to remove title bar but keep taskbar presence
        # This is more reliable than overrideredirect on Windows
        try:
            from ctypes import windll
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            # GWL_STYLE = -16, WS_CAPTION = 0xC00000
            style = windll.user32.GetWindowLongW(hwnd, -16)
            style = style & ~0xC00000
            windll.user32.SetWindowLongW(hwnd, -16, style)
        except Exception:
            # Fallback to overrideredirect if ctypes fails
            self.root.overrideredirect(True)

        # Center on screen
        self.root.update_idletasks()

        # Calculate canvas size
        self._font = tkfont.Font(
            family=FONT_FAMILY, size=FONT_SIZE, weight="normal"
        )
        self._font_bold = tkfont.Font(
            family=FONT_FAMILY, size=FONT_SIZE, weight="bold"
        )
        self._char_w = self._font.measure("M")
        self._char_h = self._font.metrics("linespace")

        # Bezel padding
        self._pad_x = 20
        self._pad_y = 16

        canvas_w = COLS * self._char_w + self._pad_x * 2
        canvas_h = (TOTAL_ROWS) * self._char_h + self._pad_y * 2 + 8

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - canvas_w) // 2
        y  = (sh - canvas_h) // 2
        self.root.geometry(f"{canvas_w}x{canvas_h}+{x}+{y}")

        # Force keyboard focus to our window
        self.root.focus_force()
        self.root.lift()
        self.root.bind("<FocusIn>", self._on_focus_in)

        # Main canvas
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_w,
            height=canvas_h,
            bg=COLOR_BG,
            highlightthickness=0
        )
        self.canvas.pack()

        # Key bindings
        self.root.bind("<Key>",        self._on_key)
        self.root.bind("<Return>",     self._on_key)
        self.root.bind("<BackSpace>",  self._on_key)
        self.root.bind("<Delete>",     self._on_key)
        self.root.bind("<Tab>",        self._on_key)
        self.root.bind("<Escape>",     self._on_key)
        self.root.bind("<Up>",         self._on_key)
        self.root.bind("<Down>",       self._on_key)
        self.root.bind("<Left>",       self._on_key)
        self.root.bind("<Right>",      self._on_key)
        self.root.bind("<Prior>",      self._on_key)   # PgUp
        self.root.bind("<Next>",       self._on_key)   # PgDn
        for i in range(1, 13):
            self.root.bind(f"<F{i}>", self._on_key)

        # Allow dragging the borderless window
        self.canvas.bind("<Button-1>",        self._on_drag_start)
        self.canvas.bind("<B1-Motion>",        self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>",  self._on_click_focus)
        self._drag_x = 0
        self._drag_y = 0

    def _build_grid(self):
        """Pre-create canvas text items for every cell."""
        self._text_ids = {}
        for row in range(TOTAL_ROWS):
            for col in range(COLS):
                x = self._pad_x + col * self._char_w
                y = self._pad_y + row * self._char_h
                # OIA row gets slightly different bg treatment
                fg = COLOR_OIA_FG if row == ROWS else COLOR_FG
                tid = self.canvas.create_text(
                    x, y,
                    text=" ",
                    font=self._font,
                    fill=fg,
                    anchor="nw"
                )
                self._text_ids[(row, col)] = tid

    def _draw_bezel(self):
        """Draw the 3270-style outer border."""
        w = self.canvas.winfo_reqwidth()
        h = self.canvas.winfo_reqheight()
        p = 4

        # Outer border
        self.canvas.create_rectangle(
            p, p, w - p, h - p,
            outline=COLOR_BORDER, width=2
        )
        # Inner border
        self.canvas.create_rectangle(
            p + 4, p + 4, w - p - 4, h - p - 4,
            outline=COLOR_FG_DIM, width=1
        )
        # OIA separator line
        oia_y = self._pad_y + ROWS * self._char_h - 2
        self.canvas.create_line(
            self._pad_x, oia_y,
            w - self._pad_x, oia_y,
            fill=COLOR_BORDER, width=1
        )

    # --- Public API ---

    def put(self, row: int, col: int, text: str,
            attr: int = ATTR_NORMAL):
        """Write text at (row, col) with given attribute."""
        for i, ch in enumerate(text):
            c = col + i
            if c >= COLS or row >= ROWS:
                break
            self._cells[(row, c)] = (ch, attr)
            self._render_cell(row, c, ch, attr)

    def clear(self):
        """Clear all data rows."""
        for row in range(ROWS):
            for col in range(COLS):
                self._cells[(row, col)] = (" ", ATTR_NORMAL)
                self._render_cell(row, col, " ", ATTR_NORMAL)

    def move_cursor(self, row: int, col: int):
        """Move the cursor to (row, col)."""
        old = self._cursor
        self._cursor = (row, col)
        # Redraw old cell to remove cursor highlight
        if old in self._cells:
            ch, attr = self._cells[old]
            self._render_cell(old[0], old[1], ch, attr)
        else:
            self._render_cell(old[0], old[1], " ", ATTR_NORMAL)
        self._render_cursor()

    def refresh(self):
        """Force a display update."""
        self.root.update_idletasks()
        self.root.update()

    def get_key(self) -> str | None:
        """
        Return next key from queue, or None if empty.
        Call refresh() first to process events.
        """
        self.refresh()
        if self._keyqueue:
            return self._keyqueue.pop(0)
        return None

    def wait_key(self) -> str:
        """Block until a key is available and return it."""
        while not self._keyqueue:
            self.refresh()
        return self._keyqueue.pop(0)

    def set_userid(self, userid: str):
        """Update userid shown in OIA."""
        self.userid = userid
        self._render_oia()

    def mainloop(self):
        """Hand control to tkinter mainloop."""
        self.root.mainloop()

    def close(self):
        """Shut down the terminal."""
        self._running = False
        self.root.destroy()

    # --- Internal Rendering ---

    def _render_cell(self, row: int, col: int,
                     ch: str, attr: int):
        tid = self._text_ids.get((row, col))
        if not tid:
            return

        if attr == ATTR_REVERSE:
            fg = COLOR_REVERSE_FG
            bg = COLOR_REVERSE_BG
        elif attr == ATTR_BOLD:
            fg = COLOR_FG_BOLD
            bg = COLOR_BG
        elif attr == ATTR_DIM:
            fg = COLOR_FG_DIM
            bg = COLOR_BG
        else:
            fg = COLOR_FG
            bg = COLOR_BG

        font = self._font_bold if attr == ATTR_BOLD else self._font

        # Draw background rectangle for reverse/highlight
        x = self._pad_x + col * self._char_w
        y = self._pad_y + row * self._char_h
        tag = f"bg_{row}_{col}"
        self.canvas.delete(tag)
        if bg != COLOR_BG:
            self.canvas.create_rectangle(
                x, y,
                x + self._char_w, y + self._char_h,
                fill=bg, outline="", tags=tag
            )
            # Raise text above background rect
            self.canvas.tag_raise(tid)

        self.canvas.itemconfig(tid, text=ch, fill=fg, font=font)

    def _render_cursor(self):
        """Draw cursor as a reverse-video block on current cell."""
        row, col = self._cursor
        if row >= ROWS:
            return
        ch, attr = self._cells.get((row, col), (" ", ATTR_NORMAL))
        # Draw as reverse
        self._render_cell(row, col, ch, ATTR_REVERSE)

    def _render_oia(self):
        """Render the OIA status line."""
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        row, col = self._cursor
        ins  = "INSERT" if self._insert else "      "
        uid  = self.userid.ljust(8)[:8]
        sys  = self.sysname.ljust(8)[:8]

        oia = (f" {sys}  {uid}  {ts}  {ins}  "
               f"ROW {row+1:02d} COL {col+1:02d}")
        oia = oia.ljust(COLS)[:COLS]

        for i, ch in enumerate(oia):
            tid = self._text_ids.get((ROWS, i))
            if tid:
                self.canvas.itemconfig(
                    tid, text=ch,
                    fill=COLOR_OIA_FG,
                    font=self._font
                )

    def _tick_oia(self):
        """Update OIA clock every second."""
        if self._text_ids:
            self._render_oia()
        self.root.after(1000, self._tick_oia)

    # --- Input Handling ---

    def _on_key(self, event):
        """Translate tkinter key event to a simple key string."""
        ks = event.keysym

        key_map = {
            "Return":    "ENTER",
            "BackSpace": "BACKSPACE",
            "Delete":    "DELETE",
            "Tab":       "TAB",
            "Escape":    "ESC",
            "Up":        "UP",
            "Down":      "DOWN",
            "Left":      "LEFT",
            "Right":     "RIGHT",
            "Prior":     "PGUP",
            "Next":      "PGDN",
        }
        for i in range(1, 13):
            key_map[f"F{i}"] = f"F{i}"

        if ks in key_map:
            self._keyqueue.append(key_map[ks])
        elif event.char and 32 <= ord(event.char) <= 126:
            self._keyqueue.append(event.char)

    def _on_focus_in(self, event):
        """Re-raise window when focus returns."""
        self.root.lift()
        self.root.focus_force()

    def _on_click_focus(self, event):
        """Grab focus back when user clicks the window."""
        self.root.focus_force()

    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _on_drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")


# --- Self Test ---
if __name__ == "__main__":
    import config
    config.load()

    term = Terminal(sysname="PY360", userid="DAVE")

    # Draw a test screen
    term.put(0,  0, "=" * 80, ATTR_REVERSE)
    term.put(0,  2, " PY360 TERMINAL ENGINE TEST ", ATTR_REVERSE)
    term.put(2,  4, "Normal text looks like this", ATTR_NORMAL)
    term.put(3,  4, "Bold text looks like this",   ATTR_BOLD)
    term.put(4,  4, "Dim text looks like this",    ATTR_DIM)
    term.put(5,  4, "Reverse text looks like this",ATTR_REVERSE)
    term.put(7,  4, "The quick brown fox jumps over the lazy dog")
    term.put(9,  4, "Press any key to exit...")
    term.put(19, 0, "=" * 80, ATTR_REVERSE)
    term.move_cursor(9, 34)
    term.refresh()

    term.wait_key()
    term.close()