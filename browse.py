"""
browse.py - PY360 ISPF Style Browser
Part of the Python Mainframe Experience Layer

Read-only file viewer using terminal.py engine.
Used for dataset browsing, HELP screens, and spool output.

Entry points:
    browse(dsn, term)        - Browse a catalog dataset
    browse_file(path, term)  - Browse any file by path
    browse_lines(lines, title, term) - Browse a list of strings
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import catalog
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE

DATA_ROWS = 20   # rows 2-21 available for data


def browse(dsn: str, term: Terminal) -> str | None:
    """
    Browse a dataset by DSN.
    Returns error message string or None on success.
    """
    path = catalog.resolve_path(dsn)
    if path is None:
        return f"DSN NOT IN CATALOG: {dsn.upper()}"
    if not os.path.exists(path):
        return f"FILE NOT FOUND: {path}"
    with open(path, "r") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]
    _browse_loop(term, dsn.upper(), lines)
    return None


def browse_file(path: str, term: Terminal,
                title: str = "") -> str | None:
    """
    Browse any file by its full path.
    """
    if not os.path.exists(path):
        return f"FILE NOT FOUND: {path}"
    with open(path, "r") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]
    _browse_loop(term, title or path, lines)
    return None


def browse_lines(lines: list, title: str, term: Terminal):
    """
    Browse an in-memory list of strings.
    Used for HELP screens and generated output.
    """
    _browse_loop(term, title, lines)


def _browse_loop(term: Terminal, title: str, lines: list):
    """Core browse display and navigation loop."""

    top_line = 0
    command  = ""
    message  = ""
    running  = True
    total    = len(lines)

    def draw():
        term.clear()

        # --- Title bar ---
        hdr   = f" BROWSE - {title} "
        right = f" LINE {top_line+1} OF {max(total,1)} "
        bar   = hdr.ljust(80 - len(right)) + right
        term.put(0, 0, bar[:80], ATTR_REVERSE)

        # --- Command line ---
        term.put(1, 0,  "COMMAND ===> ", ATTR_NORMAL)
        term.put(1, 13, f"{command:<47}", ATTR_NORMAL)
        term.put(1, 61, "SCROLL ===> PAGE", ATTR_DIM)

        # --- TOP OF DATA marker ---
        term.put(2, 0,
                 f"{'':6} {'*** TOP OF DATA ':*<{80-8}}"[:80],
                 ATTR_DIM)

        # --- Data lines ---
        shown = 0
        for row in range(DATA_ROWS - 2):  # -2 for TOP and BOTTOM markers
            data_li    = top_line + row
            screen_row = row + 3  # row 0=title, 1=cmd, 2=TOP marker

            if data_li < total:
                linenum = f"{data_li+1:06d}"
                text    = lines[data_li]
                term.put(screen_row, 0, f"{linenum} ", ATTR_DIM)
                term.put(screen_row, 7, text[:73],     ATTR_NORMAL)
                shown += 1
            else:
                break

        # --- BOTTOM OF DATA marker ---
        bot_row = shown + 3
        if bot_row < 23:
            term.put(bot_row, 0,
                     f"{'':6} {'*** BOTTOM OF DATA ':*<{80-8}}"[:80],
                     ATTR_DIM)

        # --- Message / footer ---
        if message:
            term.put(23, 0, f" {message:<78}", ATTR_REVERSE)
        else:
            term.put(23, 0,
                     " F3=EXIT  F7=UP  F8=DOWN  FIND str  TOP  BOTTOM"
                     .ljust(80), ATTR_DIM)

        term.move_cursor(1, 13 + len(command))
        term.refresh()

    def do_command(cmd: str):
        nonlocal top_line, message, running
        parts = cmd.strip().split()
        if not parts:
            return
        verb = parts[0].upper()

        if verb in ("END", "EXIT", "CANCEL", "QUIT"):
            running = False

        elif verb == "TOP":
            top_line = 0
            message  = "TOP OF DATA"

        elif verb == "BOTTOM":
            top_line = max(0, total - (DATA_ROWS - 2))
            message  = "BOTTOM OF DATA"

        elif verb == "FIND" and len(parts) >= 2:
            needle = parts[1]
            for i in range(top_line + 1, total):
                if needle.lower() in lines[i].lower():
                    top_line = i
                    message  = f"FOUND '{needle}' AT LINE {i+1}"
                    return
            # Wrap from top
            for i in range(0, top_line + 1):
                if needle.lower() in lines[i].lower():
                    top_line = i
                    message  = f"FOUND '{needle}' AT LINE {i+1} (WRAPPED)"
                    return
            message = f"'{needle}' NOT FOUND"

        elif verb == "UP":
            n        = int(parts[1]) if len(parts) > 1 else DATA_ROWS - 2
            top_line = max(0, top_line - n)

        elif verb == "DOWN":
            n        = int(parts[1]) if len(parts) > 1 else DATA_ROWS - 2
            top_line = min(max(0, total - (DATA_ROWS - 2)), top_line + n)

        else:
            message = f"UNKNOWN COMMAND: {verb}"

    # --- Input loop ---
    while running:
        draw()
        message = ""
        key = term.wait_key()

        if key == "F1":
            import help as py360help
            py360help.show("BROWSE", term)

        elif key == "F3" or key == "ESC":
            running = False

        elif key == "F7" or key == "PGUP":
            top_line = max(0, top_line - (DATA_ROWS - 2))

        elif key == "F8" or key == "PGDN":
            top_line = min(max(0, total - (DATA_ROWS - 2)),
                           top_line + (DATA_ROWS - 2))

        elif key == "UP":
            top_line = max(0, top_line - 1)

        elif key == "DOWN":
            if top_line < total - 1:
                top_line += 1

        elif key == "ENTER":
            do_command(command)
            command = ""

        elif key == "BACKSPACE":
            command = command[:-1]

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if len(command) < 47:
                command += key


# --- Self Test ---
if __name__ == "__main__":
    config.load()
    term = Terminal(sysname=config.sysname())

    # Browse a test dataset
    err = browse("USER.DAVE.SOURCE", term)
    if err:
        # Fall back to browsing some generated lines
        test_lines = [
            "PY360 BROWSE TEST",
            "=" * 60,
            "",
            "This is a test of the browse module.",
            "Use F7/F8 or PgUp/PgDn to scroll.",
            "Type FIND <string> to search.",
            "Type TOP or BOTTOM to jump.",
            "Press F3 or ESC to exit.",
            "",
        ] + [f"Line {i:04d} - The quick brown fox jumps over the lazy dog"
             for i in range(1, 50)]

        browse_lines(test_lines, "BROWSE TEST", term)

    term.close()