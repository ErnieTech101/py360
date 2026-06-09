"""
menu.py - PY360 ISPF Primary Option Menu
Part of the Python Mainframe Experience Layer

Displays the main menu and routes to subsystems.
Returns when user selects LOGOFF.
"""

import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import catalog
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE

BORDER = "=" * 80


def _draw_menu(term: Terminal, profile: dict,
               option: str, message: str):
    """Draw the ISPF primary option menu."""
    term.clear()

    ts  = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    uid = profile["userid"]

    # Title bar
    term.put(0, 0, BORDER, ATTR_REVERSE)
    title = f" PY360 - PRIMARY OPTION MENU "
    right = f" {ts} "
    term.put(0, 1,             title, ATTR_REVERSE)
    term.put(0, 80-len(right), right, ATTR_REVERSE)

    # System info line
    term.put(1, 1, f"USERID: {uid:<10}  "
                   f"PREFIX: {profile['prefix']:<20}  "
                   f"SYSNAME: {config.sysname()}", ATTR_DIM)

    # Separator
    term.put(2, 0, "-" * 80, ATTR_DIM)

    # Option field
    term.put(4,  3, "OPTION ===>", ATTR_NORMAL)
    term.put(4, 15, f"{option:<30}", ATTR_NORMAL)

    # Menu heading
    term.put(6,  3, "PY360/ISPF PRIMARY OPTION MENU", ATTR_BOLD)
    term.put(7,  3, "-" * 40, ATTR_DIM)

    # Menu options
    options = [
        ("1", "BROWSE     ", "Display data or listings"),
        ("2", "EDIT       ", "Create or change source data"),
        ("3", "UTILITIES  ", "Dataset utility functions"),
        ("4", "FOREGROUND ", "Run PY360 REXX program"),
        ("5", "BATCH      ", "Submit job via JCL"),
        ("6", "SPOOL      ", "Browse spool and job output"),
        ("7", "STATUS     ", "Display system status"),
        ("X", "EXIT ISPF  ", "Return to READY prompt"),
    ]

    for i, (key, name, desc) in enumerate(options):
        row = 9 + i
        term.put(row,  5, key,       ATTR_BOLD)
        term.put(row,  8, name,      ATTR_NORMAL)
        term.put(row, 20, desc[:28], ATTR_DIM)

    # Right panel - system info
    ts2  = datetime.datetime.now().strftime("%H:%M:%S")
    info = [
        ("User ID  .", profile["userid"]),
        ("Time . . .", ts2),
        ("Terminal .", "3278-EMU"),
        ("Language .", "ENGLISH"),
        ("Appl ID  .", "PY360"),
        ("Prefix . .", profile["prefix"]),
        ("System ID.", config.sysname()),
        ("Node . . .", config.nodename()),
        ("Release  .", "PY360 V1.0"),
    ]
    term.put(7, 57, "-" * 22, ATTR_DIM)
    for i, (label, value) in enumerate(info):
        term.put(8 + i, 57, f"{label} {value[:9]}", ATTR_NORMAL)

    # Footer
    term.put(19, 0, "-" * 80, ATTR_DIM)
    term.put(20, 1, "F1=HELP  F3=EXIT ISPF  F12=CANCEL", ATTR_DIM)

    # Message line
    if message:
        term.put(22, 3, message, ATTR_BOLD)

    # Cursor on option field
    term.move_cursor(4, 15 + len(option))
    term.refresh()


def _is_authorized(dsn: str, profile: dict, write: bool = False) -> bool:
    """
    Check if user is authorized to access a DSN.
    write=True means write/delete access (stricter).
    All users can read SYS.* datasets but not write them.
    """
    if profile.get("admin", False):
        return True
    dsn_upper = dsn.upper()
    # SYS datasets are readable by all but not writable
    if dsn_upper.startswith("SYS."):
        return not write
    return dsn_upper.startswith(profile["prefix"].upper())


def _dsn_picker(term: Terminal, profile: dict,
                prompt: str, write: bool = False) -> str | None:
    """
    Prompt for a DSN with wildcard support and authorization check.
    write=True enforces write authorization (EDIT, DELETE, COPY target).
    Returns selected DSN string or None if cancelled.
    """
    term.clear()
    term.put(5, 10, prompt, ATTR_NORMAL)
    term.put(6, 10, "DSN ===>", ATTR_NORMAL)
    term.move_cursor(6, 19)
    term.refresh()

    raw = _get_input(term, 6, 19, 44).strip().upper()
    if not raw:
        return None

    # Expand bare wildcard to user prefix
    if raw == "*":
        raw = f"{profile['prefix']}.*"

    # Wildcard search
    if "*" in raw:
        prefix  = raw.replace("*", "")
        entries = catalog.listcat(prefix)

        # Filter by authorization
        if not profile.get("admin", False):
            entries = [e for e in entries
                       if _is_authorized(e["dsn"], profile, write=write)]

        if not entries:
            term.put(9, 10, "NO DATASETS FOUND", ATTR_BOLD)
            term.put(11, 10, "Press any key...", ATTR_DIM)
            term.move_cursor(11, 27)
            term.refresh()
            term.wait_key()
            return None

        # Display selection list
        while True:
            term.clear()
            term.put(0, 0, "=" * 80, ATTR_REVERSE)
            term.put(0, 2, " DATASET SELECTION LIST ", ATTR_REVERSE)
            term.put(2, 5, f"{'#':<4} {'DATASET NAME':<44} {'RECFM':<6} LRECL",
                     ATTR_BOLD)
            term.put(3, 5, "-" * 70, ATTR_DIM)

            for i, e in enumerate(entries[:15]):
                term.put(4 + i, 5,
                         f"{i+1:<4} {e['dsn']:<44} {e['recfm']:<6} {e['lrecl']}",
                         ATTR_NORMAL)

            term.put(20, 5,  "-" * 70, ATTR_DIM)
            term.put(21, 5,  "SELECT ===>", ATTR_NORMAL)
            term.put(21, 17, "          ", ATTR_NORMAL)
            term.put(22, 5,  "Enter number to select, F3 to cancel", ATTR_DIM)
            term.move_cursor(21, 17)
            term.refresh()

            sel = _get_input(term, 21, 17, 4).strip()
            if not sel:
                return None
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(entries):
                    return entries[idx]["dsn"]
                else:
                    term.put(23, 5, "INVALID SELECTION", ATTR_BOLD)
                    term.refresh()
                    term.wait_key()
            except ValueError:
                term.put(23, 5, "PLEASE ENTER A NUMBER", ATTR_BOLD)
                term.refresh()
                term.wait_key()

    # Direct DSN - check authorization
    else:
        if not _is_authorized(raw, profile, write=write):
            term.put(9,  10, f"NOT AUTHORIZED: {raw}", ATTR_BOLD)
            term.put(10, 10, f"Your prefix is: {profile['prefix']}", ATTR_DIM)
            term.put(12, 10, "Press any key...", ATTR_DIM)
            term.move_cursor(12, 27)
            term.refresh()
            term.wait_key()
            return None
        return raw


def _get_input(term: Terminal, row: int, col: int, maxlen: int) -> str:
    """Simple single field input helper."""
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


def show(term: Terminal, profile: dict):
    """
    Display ISPF primary menu and route to subsystems.
    Returns when user logs off.
    """
    option  = ""
    message = ""

    while True:
        _draw_menu(term, profile, option, message)
        message = ""

        key = term.wait_key()

        if key == "F1":
            import help as py360help
            py360help.show("MENU", term)

        elif key == "F3" or key == "ESC":
            break

        elif key == "BACKSPACE":
            option = option[:-1]

        elif key == "ENTER":
            cmd    = option.strip().upper()
            option = ""

            if cmd in ("X", "EXIT", "END"):
                break

            elif cmd == "1":
                dsn = _dsn_picker(term, profile,
                                  "BROWSE - Enter dataset name or wildcard (*):")
                if dsn:
                    try:
                        import browse
                        err = browse.browse(dsn, term)
                        if err:
                            message = err
                    except Exception as e:
                        message = f"BROWSE ERROR: {e}"

            elif cmd == "2":
                dsn = _dsn_picker(term, profile,
                                  "EDIT - Enter dataset name or wildcard (*):")
                if dsn:
                    # If DSN doesn't exist offer to allocate it
                    if not catalog.exists(dsn):
                        term.clear()
                        term.put(5, 10, f"Dataset not found: {dsn}", ATTR_BOLD)
                        term.put(7, 10, "Allocate new dataset? (YES to confirm)", ATTR_NORMAL)
                        term.move_cursor(7, 49)
                        term.refresh()
                        ans = _get_input(term, 7, 49, 3)
                        if ans.upper() == "YES":
                            ok = catalog.allocate(dsn, recfm="FB",
                                                  lrecl=80,
                                                  description="New dataset")
                            if not ok:
                                message = f"ALLOCATE FAILED: {dsn}"
                                continue
                        else:
                            message = "EDIT CANCELLED"
                            continue
                    try:
                        import editor
                        editor.edit_tk(dsn, term)
                    except Exception as e:
                        message = f"EDIT ERROR: {e}"

            elif cmd == "3":
                try:
                    import utilities
                    utilities.show(term, profile)
                except Exception as e:
                    message = f"UTILITIES ERROR: {e}"

            elif cmd == "4":
                dsn = _dsn_picker(term, profile,
                                  "FOREGROUND - Enter REXX program dataset:",
                                  write=False)
                if dsn:
                    path = catalog.resolve_path(dsn)
                    if path:
                        try:
                            import rexx as py360rexx
                            rc = py360rexx.run_interactive(path, term)
                            message = f"REXX COMPLETE - RC={rc}"
                        except Exception as e:
                            message = f"REXX ERROR: {e}"
                    else:
                        message = f"DSN NOT IN CATALOG: {dsn}"

            elif cmd == "5":
                dsn = _dsn_picker(term, profile,
                                  "BATCH - Enter JCL dataset name:",
                                  write=False)
                if dsn:
                    path = catalog.resolve_path(dsn)
                    if path:
                        try:
                            import jcl
                            term.clear()
                            term.put(0, 0, "=" * 80, ATTR_REVERSE)
                            term.put(0, 2, " PY360 - JOB SUBMISSION ", ATTR_REVERSE)
                            term.put(2, 3, f"Submitting: {dsn}", ATTR_NORMAL)
                            term.put(3, 3, "Please wait...", ATTR_DIM)
                            term.refresh()
                            rc, log = jcl.submit_dsn(dsn, term=term)
                            # Display job log
                            term.clear()
                            term.put(0, 0, "=" * 80, ATTR_REVERSE)
                            term.put(0, 2, f" JOB LOG - RC={rc} ", ATTR_REVERSE)
                            for i, line in enumerate(log[:20]):
                                term.put(i + 2, 2, line[:76], ATTR_NORMAL)
                            if len(log) > 20:
                                term.put(22, 2,
                                         f"... {len(log)-20} more lines in spool",
                                         ATTR_DIM)
                            term.put(23, 2, "Press any key to return to menu...",
                                     ATTR_DIM)
                            term.move_cursor(23, 37)
                            term.refresh()
                            term.wait_key()
                            message = f"JOB COMPLETE - RC={rc}"
                        except Exception as e:
                            message = f"JCL ERROR: {e}"
                    else:
                        message = f"DSN NOT IN CATALOG: {dsn}"

            elif cmd == "6":
                try:
                    import spool
                    spool.show(term, profile)
                except Exception as e:
                    message = f"SPOOL ERROR: {e}"

            elif cmd == "7":
                _show_status(term, profile)

            elif cmd.startswith("HELP"):
                parts = cmd.split()
                topic = parts[1] if len(parts) > 1 else "MENU"
                import help as py360help
                py360help.show(topic, term)

            else:
                message = f"UNKNOWN OPTION: {cmd}"

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if len(option) < 10:
                option += key


def _show_status(term: Terminal, profile: dict):
    """Display system status screen."""
    import psutil

    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " PY360 SYSTEM STATUS ", ATTR_REVERSE)

    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    term.put(2,  3, f"SYSTEM NAME  : {config.sysname()}", ATTR_NORMAL)
    term.put(3,  3, f"SYSPLEX      : {config.sysplex()}",  ATTR_NORMAL)
    term.put(4,  3, f"CURRENT TIME : {ts}",                ATTR_NORMAL)
    term.put(5,  3, f"ACTIVE USER  : {profile['userid']}", ATTR_NORMAL)

    term.put(7,  3, "STORAGE:", ATTR_BOLD)
    term.put(8,  5, f"Total    : {ram.total     // (1024*1024):>8}M", ATTR_NORMAL)
    term.put(9,  5, f"Available: {ram.available  // (1024*1024):>8}M", ATTR_NORMAL)
    term.put(10, 5, f"Used     : {ram.used      // (1024*1024):>8}M", ATTR_NORMAL)

    term.put(12, 3, "DASD VOLUME C:", ATTR_BOLD)
    term.put(13, 5, f"Capacity : {disk.total // (1024*1024):>8}M", ATTR_NORMAL)
    term.put(14, 5, f"Free     : {disk.free  // (1024*1024):>8}M", ATTR_NORMAL)
    term.put(15, 5, f"Used     : {disk.used  // (1024*1024):>8}M", ATTR_NORMAL)

    term.put(17, 3, "CATALOG:", ATTR_BOLD)
    entries = catalog.listcat()
    term.put(18, 5, f"Datasets allocated: {len(entries)}", ATTR_NORMAL)

    term.put(20, 0, "-" * 80, ATTR_DIM)
    term.put(21, 3, "Press any key to return to menu...", ATTR_DIM)
    term.move_cursor(21, 38)
    term.refresh()
    term.wait_key()


# --- Self Test ---
if __name__ == "__main__":
    config.load()
    term = Terminal(sysname=config.sysname())
    profile = {"userid": "DAVE", "prefix": "USER.DAVE", "admin": False}
    show(term, profile)
    term.close()