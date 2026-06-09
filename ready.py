"""
ready.py - Faux Mainframe READY Prompt (TSO-style shell)
Part of the Python Mainframe Experience Layer

The master command interpreter. Invoke this to enter the mainframe environment.
Type HELP for available commands.
"""

import sys
import os

# Make sure catalog.py is findable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import catalog

BANNER = """
********************************************************************************
*                    PY360 - A MAINFRAME EXPERIENCE IN PYTHON                  *
*                         READY PROMPT - TSO STYLE INTERFACE                   *
********************************************************************************
"""

HELP_TEXT = """
Available Commands:
  LISTCAT [prefix]              List all datasets, optional DSN prefix filter
  LISTDS DSN(name)              Show details for a single dataset
  ALLOCATE DSN(name)            Allocate a new dataset
           [RECFM(fb|f|v|vb)]   Record format (default: FB)
           [LRECL(nn)]          Logical record length (default: 80)
           [DESC(text)]         Description
  DELETE DSN(name)              Delete a dataset
  HELP                          Show this help text
  END | LOGOFF | LOGOUT        Exit the mainframe environment
"""


# --- Command Parsers ---

def _extract(token: str, text: str) -> str | None:
    """
    Extract value from a keyword parameter like DSN(USER.DAVE.TEST).
    Returns the value string or None if token not found.
    """
    text = text.upper() if token != "DESC" else text  # preserve DESC case
    token_up = token.upper()
    idx = text.upper().find(token_up + "(")
    if idx == -1:
        return None
    start = idx + len(token) + 1
    end = text.find(")", start)
    if end == -1:
        return None
    return text[start:end].strip()


# --- Command Handlers ---

def cmd_listcat(args: str):
    prefix = args.strip()
    entries = catalog.listcat(prefix)
    if not entries:
        msg = f"No datasets found"
        if prefix:
            msg += f" matching '{prefix}'"
        print(f"  {msg}")
        return
    print()
    print(f"  {'DSN':<44}  {'RECFM':<6} {'LRECL':<6} {'CREATED':<12} DESCRIPTION")
    print(f"  {'-'*44}  {'-'*5} {'-'*5} {'-'*10} -----------")
    for e in entries:
        print(f"  {e['dsn']:<44}  {e['recfm']:<6} {e['lrecl']:<6} {e['created']:<12} {e['description']}")
    print()


def cmd_listds(args: str):
    dsn = _extract("DSN", args)
    if not dsn:
        print("  Syntax: LISTDS DSN(name)")
        return
    entry = catalog.get_entry(dsn)
    if not entry:
        print(f"  DSN NOT IN CATALOG: {dsn.upper()}")
        return
    print()
    print(f"  DSN:         {dsn.upper()}")
    print(f"  PATH:        {catalog.resolve_path(dsn)}")
    print(f"  RECFM:       {entry['recfm']}")
    print(f"  LRECL:       {entry['lrecl']}")
    print(f"  CREATED:     {entry['created']}")
    print(f"  DESCRIPTION: {entry['description']}")
    print()


def cmd_allocate(args: str):
    dsn   = _extract("DSN",   args)
    recfm = _extract("RECFM", args) or "FB"
    lrecl_str = _extract("LRECL", args) or "80"
    desc  = _extract("DESC",  args) or ""

    if not dsn:
        print("  Syntax: ALLOCATE DSN(name) [RECFM(fb)] [LRECL(80)] [DESC(text)]")
        return

    try:
        lrecl = int(lrecl_str)
    except ValueError:
        print(f"  Invalid LRECL value: {lrecl_str}")
        return

    catalog.allocate(dsn, recfm=recfm, lrecl=lrecl, description=desc)


def cmd_delete(args: str):
    dsn = _extract("DSN", args)
    if not dsn:
        print("  Syntax: DELETE DSN(name)")
        return
    # Confirm before deleting
    confirm = input(f"  Delete {dsn.upper()}? (YES to confirm): ").strip().upper()
    if confirm == "YES":
        catalog.delete(dsn)
    else:
        print("  Delete cancelled.")


# --- Main Loop ---

def main():
    print(BANNER)
    print("READY")

    while True:
        try:
            raw = input(" ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLOGOFF")
            break

        if not raw:
            print("READY")
            continue

        # Split verb from args
        parts = raw.split(None, 1)
        verb  = parts[0].upper()
        args  = parts[1] if len(parts) > 1 else ""

        if verb in ("END", "LOGOFF", "LOGOUT"):
            print("\nLOGOFF - SESSION ENDED\n")
            break
        elif verb == "HELP":
            print(HELP_TEXT)
        elif verb == "LISTCAT":
            cmd_listcat(args)
        elif verb == "LISTDS":
            cmd_listds(args)
        elif verb == "ALLOCATE":
            cmd_allocate(args)
        elif verb == "DELETE":
            cmd_delete(args)
        else:
            print(f"  UNKNOWN COMMAND: {verb}")

        print("READY")


if __name__ == "__main__":
    main()