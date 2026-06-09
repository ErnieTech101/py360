"""
editor.py - PY360 ISPF Style Editor
Part of the Python Mainframe Experience Layer

Full screen editor using terminal.py engine.
Invoked from menu.py or directly for testing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import catalog
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE

# Layout constants
LINENUM_WIDTH = 7    # "000001 "
TEXT_COL      = LINENUM_WIDTH
MAX_TEXT_COLS = 80 - LINENUM_WIDTH


def edit_tk(dsn: str, term: Terminal):
    """
    Entry point from menu.py.
    Resolve DSN and launch editor on existing terminal.
    """
    path = catalog.resolve_path(dsn)
    if path is None:
        return f"DSN NOT IN CATALOG: {dsn.upper()}"
    _editor_loop(term, dsn.upper(), path)
    return None


def edit(dsn: str):
    """
    Standalone entry point - creates its own terminal.
    Used for direct testing.
    """
    config.load()
    path = catalog.resolve_path(dsn)
    if path is None:
        return f"DSN NOT IN CATALOG: {dsn.upper()}"
    term = Terminal(sysname=config.sysname())
    _editor_loop(term, dsn.upper(), path)
    term.close()


def _editor_loop(term: Terminal, dsn: str, path: str):
    """Main editor logic."""

    # Load file
    if os.path.exists(path) and os.stat(path).st_size > 0:
        with open(path, "r") as f:
            lines = [l.rstrip("\n") for l in f.readlines()]
    else:
        lines = []

    # Editor state
    top_line  = 0       # index of first visible data line (0=TOP marker)
    cur_row   = 1       # screen row (0=cmd, 1=first data row)
    cur_col   = 0       # col in text area
    cur_mode  = 1       # 0=command line, 1=linenum area, 2=text area
    command   = ""      # primary command field
    message   = ""      # status message
    modified  = False
    clipboard = []      # copy/move buffer
    line_cmds = {}      # {line_index: cmd_string}
    running   = True

    DATA_ROWS = 20      # rows available for data (rows 2-21)

    def draw():
        term.clear()

        # --- Title bar ---
        mod_flag = " (MODIFIED)" if modified else ""
        title = f" EDIT - {dsn}{mod_flag} "
        right = f" LINE {top_line+1} COL 1 80 "
        bar   = title.ljust(80 - len(right)) + right
        term.put(0, 0, bar[:80], ATTR_REVERSE)

        # --- Command line ---
        term.put(1, 0,  "COMMAND ===> ", ATTR_NORMAL)
        term.put(1, 13, f"{command:<47}", ATTR_NORMAL)
        term.put(1, 61, "SCROLL ===> PAGE", ATTR_DIM)

        # --- Data rows ---
        for row in range(DATA_ROWS):
            li         = top_line + row
            screen_row = row + 2   # row 0=title, row 1=cmd, row 2+ = data

            if li == 0:
                marker = f"{'':6} {'*** TOP OF DATA ':*<{80-8}}"
                term.put(screen_row, 0, marker[:80], ATTR_DIM)
                continue

            data_li = li - 1  # actual index into lines[]

            if data_li < len(lines):
                lcmd    = line_cmds.get(data_li, "")
                linenum = f"{data_li+1:06d}"
                prefix  = f"{lcmd:<6} " if lcmd else f"{linenum} "
                text    = lines[data_li]
                term.put(screen_row, 0, prefix, ATTR_DIM)
                term.put(screen_row, LINENUM_WIDTH,
                         text[:80-LINENUM_WIDTH], ATTR_NORMAL)

            elif data_li == len(lines):
                marker = f"{'':6} {'*** BOTTOM OF DATA ':*<{80-8}}"
                term.put(screen_row, 0, marker[:80], ATTR_DIM)
                break

        # --- Message bar ---
        term.put(23, 0, f" {message:<78}", ATTR_REVERSE)

        # --- Cursor ---
        # screen_row: row 0=title, row 1=command, row 2=TOP OF DATA marker
        # first actual data line is screen row 3, which is cur_row=1, top_line offset 1
        if cur_mode == 0:
            term.move_cursor(1, 13 + len(command))
        elif cur_mode == 1:
            data_li = top_line + cur_row - 1
            lcmd    = line_cmds.get(data_li, "")
            term.move_cursor(cur_row + 2, len(lcmd))
        else:
            term.move_cursor(cur_row + 2, LINENUM_WIDTH + cur_col)

        term.refresh()

    def save():
        nonlocal modified, message
        with open(path, "w") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        modified = False
        message  = "FILE SAVED"

    def do_primary_cmd(cmd: str):
        nonlocal message, running, top_line, cur_row
        parts = cmd.strip().split()
        if not parts:
            return
        verb = parts[0].upper()

        if verb in ("SAVE", "FILE"):
            save()

        elif verb in ("CANCEL", "QUIT"):
            running = False

        elif verb == "END":
            if modified:
                save()
            running = False

        elif verb == "FIND" and len(parts) >= 2:
            needle = parts[1]
            for i, line in enumerate(lines):
                if needle.lower() in line.lower():
                    top_line = max(0, i)
                    cur_row  = 1
                    message  = f"FOUND '{needle}' AT LINE {i+1}"
                    return
            message = f"'{needle}' NOT FOUND"

        elif verb == "CHANGE" and len(parts) >= 3:
            needle, replacement = parts[1], parts[2]
            for i, line in enumerate(lines):
                if needle.lower() in line.lower():
                    lines[i] = line.replace(needle, replacement, 1)
                    message  = f"CHANGED LINE {i+1}"
                    return
            message = f"'{needle}' NOT FOUND"

        elif verb == "UP":
            n = int(parts[1]) if len(parts) > 1 else DATA_ROWS
            top_line = max(0, top_line - n)

        elif verb == "DOWN":
            n = int(parts[1]) if len(parts) > 1 else DATA_ROWS
            top_line = min(max(0, len(lines) - DATA_ROWS + 2), top_line + n)

        else:
            message = f"UNKNOWN COMMAND: {verb}"

    def do_line_cmds():
        nonlocal modified, message, clipboard, cur_row, cur_col
        pending = dict(line_cmds)
        line_cmds.clear()

        mm_lines = sorted([i for i, c in pending.items() if c.upper() == "MM"])
        cc_lines = sorted([i for i, c in pending.items() if c.upper() == "CC"])

        for li, cmd in sorted(pending.items()):
            c = cmd.strip().upper()

            if c == "D":
                del lines[li]
                modified = True
                message  = f"LINE {li+1} DELETED"

            elif c == "I":
                lines.insert(li + 1, "")
                modified = True
                cur_row += 1
                cur_col  = 0
                message  = f"LINE INSERTED AFTER {li+1}"

            elif c == "R":
                lines.insert(li + 1, lines[li])
                modified = True
                message  = f"LINE {li+1} REPEATED"

            elif c == "C":
                clipboard = [lines[li]]
                message   = f"LINE {li+1} COPIED - USE A OR B TO PASTE"

            elif c == "M":
                clipboard = [lines[li]]
                lines.pop(li)
                modified = True
                message  = f"LINE MOVED - USE A OR B TO PASTE"

            elif c == "A" and clipboard:
                for j, l in enumerate(clipboard):
                    lines.insert(li + 1 + j, l)
                modified  = True
                message   = f"PASTED {len(clipboard)} LINE(S) AFTER {li+1}"
                clipboard = []

            elif c == "B" and clipboard:
                for j, l in enumerate(clipboard):
                    lines.insert(li + j, l)
                modified  = True
                message   = f"PASTED {len(clipboard)} LINE(S) BEFORE {li+1}"
                clipboard = []

        if len(cc_lines) == 2:
            clipboard = lines[cc_lines[0]:cc_lines[1]+1]
            message   = f"BLOCK COPIED ({len(clipboard)} lines) - USE A OR B TO PASTE"

        if len(mm_lines) == 2:
            clipboard = lines[mm_lines[0]:mm_lines[1]+1]
            del lines[mm_lines[0]:mm_lines[1]+1]
            modified  = True
            message   = f"BLOCK MOVED ({len(clipboard)} lines) - USE A OR B TO PASTE"

    # --- Main input loop ---
    while running:
        draw()
        message = ""

        key = term.wait_key()

        if key == "F1":
            import help as py360help
            py360help.show("EDITOR", term)

        elif key == "F3":
            if modified:
                save()
            running = False

        elif key == "F4":
            running = False

        elif key == "TAB":
            # Cycle: command(0) -> linenum(1) -> text(2) -> command(0)
            cur_mode = (cur_mode + 1) % 3
            if cur_mode == 0:
                pass  # command line
            elif cur_mode == 1:
                cur_row = max(1, cur_row)  # ensure on a data row
            else:
                cur_row = max(1, cur_row)

        elif key == "UP":
            if cur_mode == 0:
                cur_mode = 2
                cur_row  = 1
            elif cur_row > 1:
                cur_row -= 1
            elif top_line > 0:
                top_line -= 1

        elif key == "DOWN":
            if cur_mode == 0:
                cur_mode = 1
                cur_row  = 1
            else:
                max_row = min(len(lines), DATA_ROWS - 1)
                if cur_row < max_row:
                    cur_row += 1
                elif top_line + DATA_ROWS <= len(lines):
                    top_line += 1

        elif key == "LEFT":
            if cur_mode == 2:
                cur_col = max(0, cur_col - 1)

        elif key == "RIGHT":
            if cur_mode == 2:
                data_li = top_line + cur_row - 1
                if data_li < len(lines):
                    cur_col = min(len(lines[data_li]), cur_col + 1)

        elif key == "PGUP":
            top_line = max(0, top_line - DATA_ROWS)
            cur_row  = 1

        elif key == "PGDN":
            top_line = min(max(0, len(lines) - DATA_ROWS + 2),
                           top_line + DATA_ROWS)
            cur_row  = 1

        elif key == "ENTER":
            if cur_mode == 0:
                do_primary_cmd(command)
                command = ""
            else:
                do_line_cmds()

        elif key == "BACKSPACE":
            if cur_mode == 0:
                command = command[:-1]
            elif cur_mode == 1:
                data_li = top_line + cur_row - 1
                lcmd = line_cmds.get(data_li, "")
                if lcmd:
                    line_cmds[data_li] = lcmd[:-1]
                    if not line_cmds[data_li]:
                        del line_cmds[data_li]
            else:
                data_li = top_line + cur_row - 1
                if data_li < len(lines) and cur_col > 0:
                    lines[data_li] = (lines[data_li][:cur_col-1] +
                                      lines[data_li][cur_col:])
                    cur_col  -= 1
                    modified  = True

        elif key == "DELETE":
            if cur_mode == 2:
                data_li = top_line + cur_row - 1
                if data_li < len(lines):
                    lines[data_li] = (lines[data_li][:cur_col] +
                                      lines[data_li][cur_col+1:])
                    modified = True

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if cur_mode == 0:
                command += key
            elif cur_mode == 1:
                # Typing in line number area = line command
                data_li = top_line + cur_row - 1
                if 0 <= data_li < len(lines):
                    lcmd = line_cmds.get(data_li, "")
                    if len(lcmd) < 6:
                        line_cmds[data_li] = lcmd + key.upper()
            else:
                data_li = top_line + cur_row - 1
                if data_li < len(lines):
                    lines[data_li] = (lines[data_li][:cur_col] +
                                      key +
                                      lines[data_li][cur_col:])
                    cur_col  += 1
                    modified  = True
                elif data_li == len(lines):
                    lines.append(key)
                    cur_col  = 1
                    modified = True


if __name__ == "__main__":
    edit("USER.DAVE.SOURCE")