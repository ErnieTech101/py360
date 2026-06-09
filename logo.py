"""
logo.py - PY360 Logo and Login Screen
Part of the Python Mainframe Experience Layer

Displays the PY360 splash screen and collects
userid/password for login. Returns a user profile dict.
Uses terminal.py instead of curses.
"""

import os
import json
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE

USERS_DIR = os.path.join(config.SIM_ROOT, "users")

# --- ASCII Art Logo ---
LOGO = [
    r"      ########  ##    ##       ##  #######   #######    #####      ",
    r"      ##     ##  ##  ##       ##  ##     ## ##     ##  ##   ##     ",
    r"      ##     ##   ####       ##          ## ##        ##     ##    ",
    r"      ########     ##       ##     #######  ########  ##     ##    ",
    r"      ##           ##      ##            ## ##     ## ##     ##    ",
    r"      ##           ##     ##      ##     ## ##     ##  ##   ##     ",
    r"      ##           ##    ##        #######   #######    #####      ",
]

SUBTITLE = "Python/360 MVS OS Mainframe Simulator  V1.0"
BORDER   = "=" * 80


def _draw_logo(term: Terminal, userid: str, password: str,
               field: int, message: str):
    """Draw the full logo and login screen."""
    term.clear()

    # Top border
    term.put(0, 0, BORDER, ATTR_REVERSE)

    # Logo rows centered vertically starting row 2
    for i, line in enumerate(LOGO):
        term.put(i + 2, 0, line.center(80), ATTR_NORMAL)

    # Subtitle
    term.put(11, 0, SUBTITLE.center(80), ATTR_BOLD)

    # Separator
    term.put(13, 0, "-" * 80, ATTR_DIM)

    # Login fields
    term.put(15, 20, "USERID   ===> ", ATTR_NORMAL)
    term.put(15, 34, f"{userid:<20}",  ATTR_NORMAL)

    term.put(16, 20, "PASSWORD ===> ", ATTR_NORMAL)
    term.put(16, 34, f"{'*' * len(password):<20}", ATTR_NORMAL)

    # Message line
    if message:
        term.put(18, 20, message, ATTR_BOLD)

    # Bottom border
    term.put(19, 0, BORDER, ATTR_REVERSE)

    # Position cursor on active field
    if field == 0:
        term.move_cursor(15, 34 + len(userid))
    else:
        term.move_cursor(16, 34 + len(password))

    term.refresh()


def _get_or_create_user(userid: str) -> dict:
    """Load or create a user profile JSON."""
    os.makedirs(USERS_DIR, exist_ok=True)
    path = os.path.join(USERS_DIR, f"{userid.lower()}.json")

    if os.path.exists(path):
        profile = json.load(open(path, "r"))
        profile["_new_user"] = False
        return profile

    # New user — create default profile
    profile = {
        "userid":     userid.upper(),
        "prefix":     f"USER.{userid.upper()}",
        "lastlogin":  "NEVER",
        "lrecl":      80,
        "recfm":      "FB",
        "scrollmode": "PAGE"
    }
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)

    # Auto-create user dataset directory
    parts = profile["prefix"].split(".")
    user_dir = os.path.join(config.SIM_ROOT, "datasets", *parts)
    os.makedirs(user_dir, exist_ok=True)

    profile["_new_user"] = True
    return profile


def _update_lastlogin(profile: dict):
    """Stamp last login time into user profile."""
    profile["lastlogin"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(USERS_DIR, f"{profile['userid'].lower()}.json")
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)


def show(term: Terminal) -> dict | None:
    """
    Display logo and login screen on existing terminal.
    Returns user profile dict on success, None if ESC pressed.
    """
    userid   = ""
    password = ""
    field    = 0
    message  = ""

    while True:
        _draw_logo(term, userid, password, field, message)
        message = ""

        key = term.wait_key()

        if key == "ESC":
            return None

        elif key in ("TAB", "DOWN", "ENTER") and field == 0:
            if userid.strip():
                field = 1
            else:
                message = "Please enter a USERID"

        elif key == "UP" and field == 1:
            field = 0

        elif key == "ENTER" and field == 1:
            if not userid.strip():
                field   = 0
                message = "Please enter a USERID"
            else:
                profile = _get_or_create_user(userid.strip())
                _update_lastlogin(profile)
                term.set_userid(profile["userid"])
                # Flag new user for welcome screen
                return profile

        elif key == "BACKSPACE":
            if field == 0 and userid:
                userid = userid[:-1]
            elif field == 1 and password:
                password = password[:-1]

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if field == 0 and len(userid) < 20:
                userid += key
            elif field == 1 and len(password) < 20:
                password += key


# --- Self Test ---
if __name__ == "__main__":
    config.load()
    term = Terminal(sysname=config.sysname())
    profile = show(term)
    if profile:
        term.clear()
        term.put(5,  10, f"Welcome to PY360, {profile['userid']}!", ATTR_BOLD)
        if profile.get("_new_user"):
            term.put(7,  10, "NEW USERID - PROFILE AND DATASET DIRECTORY CREATED", ATTR_BOLD)
            term.put(8,  10, f"DSN Prefix : {profile['prefix']}",   ATTR_NORMAL)
        else:
            term.put(7,  10, f"Last login : {profile['lastlogin']}", ATTR_NORMAL)
            term.put(8,  10, f"DSN Prefix : {profile['prefix']}",    ATTR_NORMAL)
        term.put(10, 10, "Press any key to continue...",             ATTR_DIM)
        term.move_cursor(10, 36)
        term.refresh()
        term.wait_key()
    term.close()