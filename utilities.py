"""
utilities.py - PY360 Dataset Utilities
Part of the Python Mainframe Experience Layer

Provides dataset management functions accessible
from the ISPF primary menu option 3.
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import catalog
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE


def show(term: Terminal, profile: dict):
    """Display utilities submenu and handle selection."""
    option  = ""
    message = ""

    while True:
        _draw_menu(term, option, message, profile)
        message = ""
        key = term.wait_key()

        if key == "F1":
            import help as py360help
            py360help.show("UTIL", term)

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
                _listcat(term, profile)
            elif cmd == "2":
                message = _allocate(term, profile)
            elif cmd == "3":
                message = _delete(term, profile)
            elif cmd == "4":
                message = _rename(term, profile)
            elif cmd == "5":
                message = _copy(term, profile)
            elif cmd == "6":
                _listds(term, profile)
            else:
                message = f"UNKNOWN OPTION: {cmd}"

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if len(option) < 10:
                option += key


def _draw_menu(term: Terminal, option: str,
               message: str, profile: dict):
    """Draw the utilities submenu."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " PY360 - DATASET UTILITIES ", ATTR_REVERSE)

    term.put(1, 1, f"USERID: {profile['userid']:<10}  "
                   f"PREFIX: {profile['prefix']}", ATTR_DIM)
    term.put(2, 0, "-" * 80, ATTR_DIM)

    term.put(4,  3, "OPTION ===>", ATTR_NORMAL)
    term.put(4, 15, f"{option:<20}", ATTR_NORMAL)

    term.put(6,  3, "DATASET UTILITIES", ATTR_BOLD)
    term.put(7,  3, "-" * 40, ATTR_DIM)

    options = [
        ("1", "LISTCAT  ", "List datasets in catalog"),
        ("2", "ALLOCATE ", "Create a new dataset"),
        ("3", "DELETE   ", "Delete a dataset"),
        ("4", "RENAME   ", "Rename a dataset"),
        ("5", "COPY     ", "Copy one dataset to another"),
        ("6", "LISTDS   ", "Display dataset details"),
        ("X", "EXIT     ", "Return to main menu"),
    ]

    for i, (key, name, desc) in enumerate(options):
        row = 9 + i
        term.put(row,  5, key,  ATTR_BOLD)
        term.put(row,  8, name, ATTR_NORMAL)
        term.put(row, 20, desc, ATTR_DIM)

    term.put(19, 0, "-" * 80, ATTR_DIM)
    term.put(20, 1, "F1=HELP  F3=EXIT", ATTR_DIM)

    if message:
        term.put(22, 3, message, ATTR_BOLD)

    term.move_cursor(4, 15 + len(option))
    term.refresh()


def _get_input(term: Terminal, row: int, col: int,
               maxlen: int, default: str = "") -> str:
    """Single field input with optional default."""
    value = default
    term.put(row, col, f"{value:<{maxlen}}", ATTR_NORMAL)
    term.move_cursor(row, col + len(value))
    term.refresh()
    while True:
        term.put(row, col, f"{value:<{maxlen}}", ATTR_NORMAL)
        term.move_cursor(row, col + len(value))
        term.refresh()
        key = term.wait_key()
        if key == "ENTER":
            return value.strip()
        elif key in ("F3", "ESC"):
            return ""
        elif key == "BACKSPACE" and value:
            value = value[:-1]
        elif len(key) == 1 and len(value) < maxlen:
            value += key


def _confirm(term: Terminal, row: int, prompt: str) -> bool:
    """Ask YES/NO confirmation. Returns True if YES."""
    term.put(row, 3, f"{prompt} (YES to confirm): ", ATTR_BOLD)
    ans = _get_input(term, row, 3 + len(prompt) + 19, 3)
    return ans.upper() == "YES"


def _is_authorized(dsn: str, profile: dict, write: bool = False) -> bool:
    """
    Check if user is authorized to access a DSN.
    write=True means write/delete access (stricter).
    All users can read SYS.* datasets but not write them.
    """
    if profile.get("admin", False):
        return True
    dsn_upper = dsn.upper()
    if dsn_upper.startswith("SYS."):
        return not write
    return dsn_upper.startswith(profile["prefix"].upper())


# --- Utility Functions ---

def _listcat(term: Terminal, profile: dict):
    """List datasets with optional prefix filter."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " LISTCAT ", ATTR_REVERSE)
    term.put(2, 3, "PREFIX ===>", ATTR_NORMAL)
    term.put(2, 15, f"{profile['prefix']:<40}", ATTR_NORMAL)
    term.put(3, 3, "(Press ENTER for your prefix, or type a different prefix)", ATTR_DIM)
    term.move_cursor(2, 15)
    term.refresh()

    prefix = _get_input(term, 2, 15, 44, profile["prefix"])
    if not prefix:
        prefix = profile["prefix"]
    prefix = prefix.upper().strip()

    # Get matching entries
    entries = catalog.listcat(prefix)

    # Filter by authorization:
    # Admin sees everything, regular users see own + SYS.*
    if not profile.get("admin", False):
        entries = [e for e in entries
                   if e["dsn"].upper().startswith(profile["prefix"].upper())
                   or e["dsn"].upper().startswith("SYS.")]

    # Display results
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, f" LISTCAT - PREFIX: {prefix} ", ATTR_REVERSE)
    term.put(2, 1, f"{'DATASET NAME':<24} {'RECFM':<6} {'LRECL':<6} {'CREATED':<12} DESCRIPTION",
             ATTR_BOLD)
    term.put(3, 1, "-" * 78, ATTR_DIM)

    if not entries:
        term.put(5, 3, "NO DATASETS FOUND", ATTR_BOLD)
    else:
        for i, e in enumerate(entries[:16]):
            row = 4 + i
            term.put(row, 1,
                     f"{e['dsn'][:23]:<24} {e['recfm']:<6} {e['lrecl']:<6} "
                     f"{e['created']:<12} {e['description'][:24]}",
                     ATTR_NORMAL)
        if len(entries) > 16:
            term.put(21, 3, f"... {len(entries)-16} more datasets not shown", ATTR_DIM)

    term.put(22, 1, f"Total: {len(entries)} dataset(s) found", ATTR_DIM)
    term.put(23, 1, "Press any key to continue...", ATTR_DIM)
    term.move_cursor(23, 30)
    term.refresh()
    term.wait_key()


def _allocate(term: Terminal, profile: dict) -> str:
    """Allocate a new dataset."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " ALLOCATE - CREATE NEW DATASET ", ATTR_REVERSE)

    term.put(3,  3, "DSN   ===>", ATTR_NORMAL)
    term.put(4,  3, "RECFM ===>", ATTR_NORMAL)
    term.put(5,  3, "LRECL ===>", ATTR_NORMAL)
    term.put(6,  3, "DESC  ===>", ATTR_NORMAL)
    term.put(8,  3, "Press F3 to cancel", ATTR_DIM)

    term.put(3, 14, f"{profile['prefix']}.", ATTR_NORMAL)
    dsn_start_col = 14 + len(profile["prefix"]) + 1
    term.move_cursor(3, dsn_start_col)
    term.refresh()

    dsn_suffix = _get_input(term, 3, dsn_start_col, 30)
    if not dsn_suffix:
        return "ALLOCATE CANCELLED"
    dsn = f"{profile['prefix']}.{dsn_suffix}".upper()

    term.put(4, 14, "FB", ATTR_NORMAL)
    term.move_cursor(4, 14)
    term.refresh()
    recfm = _get_input(term, 4, 14, 4, "FB") or "FB"

    term.put(5, 14, "80", ATTR_NORMAL)
    term.move_cursor(5, 14)
    term.refresh()
    lrecl_str = _get_input(term, 5, 14, 6, "80") or "80"

    term.move_cursor(6, 14)
    term.refresh()
    desc = _get_input(term, 6, 14, 40)

    try:
        lrecl = int(lrecl_str)
    except ValueError:
        return f"INVALID LRECL: {lrecl_str}"

    ok = catalog.allocate(dsn, recfm=recfm, lrecl=lrecl, description=desc)
    if ok:
        return f"ALLOCATED: {dsn}"
    else:
        return f"ALLOCATE FAILED: {dsn} (already exists?)"


def _delete(term: Terminal, profile: dict) -> str:
    """Delete a dataset."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " DELETE DATASET ", ATTR_REVERSE)
    term.put(3, 3, "DSN ===>", ATTR_NORMAL)
    term.move_cursor(3, 12)
    term.refresh()

    dsn = _get_input(term, 3, 12, 44).upper()
    if not dsn:
        return "DELETE CANCELLED"

    if not _is_authorized(dsn, profile, write=True):
        return f"NOT AUTHORIZED: {dsn}"

    if not catalog.exists(dsn):
        return f"DSN NOT FOUND: {dsn}"

    term.put(5, 3, f"Dataset: {dsn}", ATTR_BOLD)
    if _confirm(term, 7, f"DELETE {dsn}?"):
        ok = catalog.delete(dsn)
        return f"DELETED: {dsn}" if ok else f"DELETE FAILED: {dsn}"
    return "DELETE CANCELLED"


def _rename(term: Terminal, profile: dict) -> str:
    """Rename a dataset."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " RENAME DATASET ", ATTR_REVERSE)
    term.put(3, 3, "FROM DSN ===>", ATTR_NORMAL)
    term.put(4, 3, "TO   DSN ===>", ATTR_NORMAL)
    term.move_cursor(3, 17)
    term.refresh()

    from_dsn = _get_input(term, 3, 17, 44).upper()
    if not from_dsn:
        return "RENAME CANCELLED"

    if not _is_authorized(from_dsn, profile, write=True):
        return f"NOT AUTHORIZED: {from_dsn}"

    if not catalog.exists(from_dsn):
        return f"DSN NOT FOUND: {from_dsn}"

    term.move_cursor(4, 17)
    term.refresh()
    to_dsn = _get_input(term, 4, 17, 44).upper()
    if not to_dsn:
        return "RENAME CANCELLED"

    if not _is_authorized(to_dsn, profile, write=True):
        return f"NOT AUTHORIZED FOR TARGET: {to_dsn}"

    entry    = catalog.get_entry(from_dsn)
    old_path = catalog.resolve_path(from_dsn)
    ok       = catalog.allocate(to_dsn,
                                recfm=entry["recfm"],
                                lrecl=entry["lrecl"],
                                description=entry["description"])
    if not ok:
        return f"TARGET ALREADY EXISTS: {to_dsn}"

    new_path = catalog.resolve_path(to_dsn)
    if os.path.exists(old_path):
        shutil.copy2(old_path, new_path)
    catalog.delete(from_dsn)
    return f"RENAMED: {from_dsn} -> {to_dsn}"


def _copy(term: Terminal, profile: dict) -> str:
    """Copy a dataset."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " COPY DATASET ", ATTR_REVERSE)
    term.put(3, 3, "FROM DSN ===>", ATTR_NORMAL)
    term.put(4, 3, "TO   DSN ===>", ATTR_NORMAL)
    term.move_cursor(3, 17)
    term.refresh()

    from_dsn = _get_input(term, 3, 17, 44).upper()
    if not from_dsn:
        return "COPY CANCELLED"

    if not _is_authorized(from_dsn, profile, write=False):
        return f"NOT AUTHORIZED: {from_dsn}"

    if not catalog.exists(from_dsn):
        return f"DSN NOT FOUND: {from_dsn}"

    term.move_cursor(4, 17)
    term.refresh()
    to_dsn = _get_input(term, 4, 17, 44).upper()
    if not to_dsn:
        return "COPY CANCELLED"

    if not _is_authorized(to_dsn, profile, write=True):
        return f"NOT AUTHORIZED FOR TARGET: {to_dsn}"

    entry    = catalog.get_entry(from_dsn)
    old_path = catalog.resolve_path(from_dsn)
    ok       = catalog.allocate(to_dsn,
                                recfm=entry["recfm"],
                                lrecl=entry["lrecl"],
                                description=f"COPY OF {from_dsn}")
    if not ok:
        return f"TARGET ALREADY EXISTS: {to_dsn}"

    new_path = catalog.resolve_path(to_dsn)
    if os.path.exists(old_path):
        shutil.copy2(old_path, new_path)
    return f"COPIED: {from_dsn} -> {to_dsn}"


def _listds(term: Terminal, profile: dict):
    """Display detailed info for a single dataset."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " LISTDS - DATASET DETAILS ", ATTR_REVERSE)
    term.put(3, 3, "DSN ===>", ATTR_NORMAL)
    term.move_cursor(3, 12)
    term.refresh()

    dsn = _get_input(term, 3, 12, 44).upper()
    if not dsn:
        return

    if not _is_authorized(dsn, profile, write=False):
        term.put(5, 3, f"NOT AUTHORIZED: {dsn}", ATTR_BOLD)
        term.put(7, 3, "Press any key...", ATTR_DIM)
        term.move_cursor(7, 20)
        term.refresh()
        term.wait_key()
        return

    entry = catalog.get_entry(dsn)
    if not entry:
        term.put(5, 3, f"DSN NOT IN CATALOG: {dsn}", ATTR_BOLD)
        term.put(7, 3, "Press any key...", ATTR_DIM)
        term.move_cursor(7, 20)
        term.refresh()
        term.wait_key()
        return

    path  = catalog.resolve_path(dsn)
    size  = os.path.getsize(path) if os.path.exists(path) else 0
    lines = 0
    if os.path.exists(path) and size > 0:
        with open(path, "r") as f:
            lines = sum(1 for _ in f)

    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " LISTDS - DATASET DETAILS ", ATTR_REVERSE)

    term.put(2,  3, "DATASET NAME :", ATTR_DIM)
    term.put(2, 18, dsn,             ATTR_BOLD)
    term.put(4,  3, f"RECFM        : {entry['recfm']}",        ATTR_NORMAL)
    term.put(5,  3, f"LRECL        : {entry['lrecl']}",        ATTR_NORMAL)
    term.put(6,  3, f"CREATED      : {entry['created']}",      ATTR_NORMAL)
    term.put(7,  3, f"DESCRIPTION  : {entry['description']}",  ATTR_NORMAL)
    term.put(8,  3, f"SIZE (bytes) : {size}",                  ATTR_NORMAL)
    term.put(9,  3, f"LINES        : {lines}",                 ATTR_NORMAL)
    term.put(10, 3, f"PATH         : {os.path.relpath(path, config.SIM_ROOT)}",
             ATTR_DIM)

    term.put(12, 0, "-" * 80, ATTR_DIM)
    term.put(13, 3, "Press any key to continue...", ATTR_DIM)
    term.move_cursor(13, 32)
    term.refresh()
    term.wait_key()


# --- Self Test ---
if __name__ == "__main__":
    config.load()
    term = Terminal(sysname=config.sysname())
    profile = {"userid": "DAVE", "prefix": "USER.DAVE", "admin": False}
    show(term, profile)
    term.close()