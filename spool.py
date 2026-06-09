"""
spool.py - PY360 Spool Viewer
Part of the Python Mainframe Experience Layer

Displays spool output from REXX programs and batch jobs.
Simulates the IBM 1403 printer output experience.

Spool files:
    spool\\printout.txt  - Main printer output (device 00E / PRT001)
    spool\\punch.txt     - Card punch output   (device 00F / PCH001)
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import browse
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE

SPOOL_DIR   = os.path.join(config.SIM_ROOT, "spool")
PRINTER_FILE = os.path.join(SPOOL_DIR, "printout.txt")
PUNCH_FILE   = os.path.join(SPOOL_DIR, "punch.txt")


def show(term: Terminal, profile: dict):
    """Display spool menu and handle selection."""
    option  = ""
    message = ""

    while True:
        _draw_menu(term, option, message)
        message = ""
        key = term.wait_key()

        if key == "F1":
            import help as py360help
            py360help.show("SPOOL", term)

        elif key in ("F3", "ESC"):
            break

        elif key == "BACKSPACE":
            option = option[:-1]

        elif key == "ENTER":
            cmd    = option.strip().upper()
            option = ""

            if cmd in ("X", "EXIT", "END"):
                break

            elif cmd == "1":
                _view_spool(term, PRINTER_FILE, "PRT001 - PRINTER OUTPUT")

            elif cmd == "2":
                _view_spool(term, PUNCH_FILE, "PCH001 - PUNCH OUTPUT")

            elif cmd == "3":
                message = _purge(term, PRINTER_FILE, "printer spool")

            elif cmd == "4":
                message = _purge(term, PUNCH_FILE, "punch spool")

            elif cmd == "5":
                message = _purge_all(term)

            else:
                message = f"UNKNOWN OPTION: {cmd}"

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if len(option) < 10:
                option += key


def _draw_menu(term: Terminal, option: str, message: str):
    """Draw the spool viewer menu."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " PY360 - SPOOL VIEWER ", ATTR_REVERSE)
    term.put(2, 0, "-" * 80, ATTR_DIM)

    term.put(4,  3, "OPTION ===>", ATTR_NORMAL)
    term.put(4, 15, f"{option:<20}", ATTR_NORMAL)

    term.put(6,  3, "SPOOL AND OUTPUT MANAGEMENT", ATTR_BOLD)
    term.put(7,  3, "-" * 40, ATTR_DIM)

    # Show spool file sizes
    prt_size  = _get_spool_info(PRINTER_FILE)
    pch_size  = _get_spool_info(PUNCH_FILE)

    options = [
        ("1", "VIEW PRINTER ", f"Browse printer spool  {prt_size}"),
        ("2", "VIEW PUNCH   ", f"Browse punch output   {pch_size}"),
        ("3", "PURGE PRINTER", "Clear printer spool"),
        ("4", "PURGE PUNCH  ", "Clear punch spool"),
        ("5", "PURGE ALL    ", "Clear all spool files"),
        ("X", "EXIT         ", "Return to main menu"),
    ]

    for i, (key, name, desc) in enumerate(options):
        row = 9 + i
        term.put(row,  5, key,  ATTR_BOLD)
        term.put(row,  8, name, ATTR_NORMAL)
        term.put(row, 22, desc, ATTR_DIM)

    term.put(19, 0, "-" * 80, ATTR_DIM)
    term.put(20, 1, "F1=HELP  F3=EXIT", ATTR_DIM)

    if message:
        term.put(22, 3, message, ATTR_BOLD)

    term.move_cursor(4, 15 + len(option))
    term.refresh()


def _get_spool_info(path: str) -> str:
    """Return a short status string for a spool file."""
    if not os.path.exists(path):
        return "(empty)"
    size  = os.path.getsize(path)
    if size == 0:
        return "(empty)"
    lines = 0
    with open(path, "r") as f:
        lines = sum(1 for _ in f)
    kb = size // 1024
    return f"({lines} lines, {kb}KB)"


def _view_spool(term: Terminal, path: str, title: str):
    """View a spool file using the browse engine."""
    os.makedirs(SPOOL_DIR, exist_ok=True)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        # Show empty spool message
        browse.browse_lines(
            ["", "  *** SPOOL FILE IS EMPTY ***", ""],
            title, term
        )
        return
    browse.browse_file(path, term, title=title)


def _purge(term: Terminal, path: str, label: str) -> str:
    """Purge a single spool file after confirmation."""
    term.clear()
    term.put(5,  3, f"PURGE {label.upper()}", ATTR_BOLD)
    term.put(7,  3, f"This will clear all output in {label}.", ATTR_NORMAL)
    term.put(9,  3, "Type YES to confirm, or press ENTER to cancel:", ATTR_NORMAL)
    term.move_cursor(9, 50)
    term.refresh()

    ans = _get_input(term, 9, 50, 3)
    if ans.upper() == "YES":
        try:
            os.makedirs(SPOOL_DIR, exist_ok=True)
            open(path, "w").close()
            return f"{label.upper()} PURGED"
        except Exception as e:
            return f"PURGE FAILED: {e}"
    return "PURGE CANCELLED"


def _purge_all(term: Terminal) -> str:
    """Purge all spool files after confirmation."""
    term.clear()
    term.put(5,  3, "PURGE ALL SPOOL FILES", ATTR_BOLD)
    term.put(7,  3, "This will clear ALL spool output.", ATTR_NORMAL)
    term.put(9,  3, "Type YES to confirm, or press ENTER to cancel:", ATTR_NORMAL)
    term.move_cursor(9, 50)
    term.refresh()

    ans = _get_input(term, 9, 50, 3)
    if ans.upper() == "YES":
        try:
            os.makedirs(SPOOL_DIR, exist_ok=True)
            open(PRINTER_FILE, "w").close()
            open(PUNCH_FILE,   "w").close()
            return "ALL SPOOL FILES PURGED"
        except Exception as e:
            return f"PURGE FAILED: {e}"
    return "PURGE CANCELLED"


def _get_input(term: Terminal, row: int, col: int, maxlen: int) -> str:
    """Simple single field input."""
    value = ""
    while True:
        term.put(row, col, f"{value:<{maxlen}}", ATTR_NORMAL)
        term.move_cursor(row, col + len(value))
        term.refresh()
        key = term.wait_key()
        if key == "ENTER":
            return value
        elif key in ("F3", "ESC"):
            return ""
        elif key == "BACKSPACE" and value:
            value = value[:-1]
        elif len(key) == 1 and len(value) < maxlen:
            value += key


def write_to_printer(lines: list, job_name: str = "PY360"):
    """
    Write output lines to the printer spool file.
    Formats with 1403-style header and page breaks.
    Called by REXX interpreter and JCL processor.
    """
    os.makedirs(SPOOL_DIR, exist_ok=True)
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time = datetime.datetime.now().strftime("%H:%M:%S")

    with open(PRINTER_FILE, "a") as f:
        # 1403 style job header
        f.write("1" + "=" * 79 + "\n")
        f.write(f" JOB: {job_name:<20} DATE: {date}  TIME: {time}\n")
        f.write(" " + "=" * 79 + "\n")
        f.write("-\n")

        # Write output lines with ASA carriage control
        line_count = 0
        page       = 1
        for line in lines:
            # Check for ASA carriage control character
            if line and line[0] in ("1", "0", "-", " "):
                cc   = line[0]
                text = line[1:]
            else:
                cc   = " "
                text = line

            if cc == "1":
                # Skip to new page
                f.write(f"1{'='*30} PAGE {page:04d} {'='*30}\n")
                page += 1
                line_count = 0
                f.write(f" {text}\n")
            elif cc == "0":
                # Double space
                f.write(f"\n {text}\n")
            elif cc == "-":
                # Triple space
                f.write(f"\n\n {text}\n")
            else:
                # Single space
                f.write(f" {text}\n")

            line_count += 1

        # Job trailer
        f.write("-\n")
        f.write(f"1{'='*79}\n")
        f.write(f" END OF JOB: {job_name:<20} LINES: {line_count}\n")
        f.write(" " + "=" * 79 + "\n")


# --- Wire into menu option 6 ---
if __name__ == "__main__":
    config.load()
    term = Terminal(sysname=config.sysname())
    profile = {"userid": "DAVE", "prefix": "USER.DAVE", "admin": False}
    show(term, profile)
    term.close()