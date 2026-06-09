"""
py360.py - PY360 Master Bootstrap
Part of the Python Mainframe Experience Layer

Entry point for the entire PY360 system.
Run this to start PY360:
    python py360.py

Boot sequence:
    Boot prompt  - Blinking cursor, awaits IPL command
    IPL          - System initialization sequence
    Login        - Logo and login screen
    ISPF Menu    - Primary option menu
    READY        - Post-logoff command prompt
    Shutdown     - Graceful system shutdown
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import logo
from terminal import Terminal, ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE


# -------------------------------------------------------------------
# BOOT PROMPT
# -------------------------------------------------------------------

def boot_prompt():
    """
    Display a plain black screen with a blinking cursor.
    Waits for the user to type IPL NNN.
    Returns the IPL address entered.
    """
    # Plain CMD window - before terminal opens
    # Clear screen
    os.system("cls")

    # Blink cursor and wait for IPL command
    import msvcrt
    import threading

    command = ""
    blink   = [True]
    done    = [False]

    def blink_cursor():
        while not done[0]:
            if blink[0]:
                print(f"\r{command}_", end="", flush=True)
            else:
                print(f"\r{command} ", end="", flush=True)
            blink[0] = not blink[0]
            time.sleep(0.5)

    blink_thread = threading.Thread(target=blink_cursor, daemon=True)
    blink_thread.start()

    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                done[0] = True
                print()
                parts = command.strip().upper().split()
                if parts and parts[0] == "IPL":
                    addr = parts[1] if len(parts) > 1 else "201"
                    return addr
                else:
                    # Not an IPL command - show brief error and restart
                    print(f"Unknown command: {command}")
                    time.sleep(1)
                    os.system("cls")
                    command = ""
                    done[0] = False
                    blink[0] = True
                    blink_thread = threading.Thread(target=blink_cursor, daemon=True)
                    blink_thread.start()
            elif ch == '\b':
                if command:
                    command = command[:-1]
            elif ch.isprintable():
                command += ch.upper()


# -------------------------------------------------------------------
# SHUTDOWN SEQUENCE
# -------------------------------------------------------------------

def shutdown(term: Terminal):
    """Display shutdown sequence then close terminal."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " PY360 SYSTEM SHUTDOWN ", ATTR_REVERSE)

    messages = [
        "SHUTDOWN INITIATED BY OPERATOR",
        "DRAINING JES2 INITIATORS...",
        "JES2 CHECKPOINT COMPLETE",
        "SPOOL FILES SECURED",
        "ALL DATASETS SYNCHRONIZED",
        "DEVICES VARIED OFFLINE",
        "NUCLEUS RELEASED",
        "PY360 SHUTDOWN COMPLETE - GOODBYE",
    ]

    for i, msg in enumerate(messages):
        term.put(i + 3, 3, f"PY360I {msg}", ATTR_NORMAL)
        term.refresh()
        time.sleep(0.5)

    term.put(13, 3, "=" * 40, ATTR_DIM)
    term.put(14, 3, "SYSTEM HALTED", ATTR_BOLD)
    term.refresh()
    time.sleep(2)
    term.close()


# -------------------------------------------------------------------
# READY PROMPT
# -------------------------------------------------------------------

def ready_prompt(term: Terminal, profile: dict) -> str:
    """
    Display the READY prompt after exiting ISPF.
    Returns: 'logon', 'shutdown'
    """
    command = ""
    message = ""
    current_profile = profile

    while True:
        _draw_ready(term, command, message, current_profile)
        message = ""
        key = term.wait_key()

        if key == "ENTER":
            cmd = command.strip().upper()
            command = ""

            if cmd == "LOGOFF":
                # Clear userid from OIA and stay at READY
                current_profile = {}
                term.set_userid("")
                message = "LOGGED OFF - ENTER LOGON TO CONTINUE"

            elif cmd in ("LOGON", "TSO"):
                return "logon"

            elif cmd == "APPLS":
                if current_profile:
                    return "appls"
                else:
                    message = "NOT LOGGED ON - ENTER LOGON FIRST"

            elif cmd == "SHUTDOWN":
                return "shutdown"

            elif cmd == "":
                pass

            else:
                message = f"UNKNOWN COMMAND: {cmd}"

        elif key == "BACKSPACE":
            command = command[:-1]

        elif len(key) == 1 and 32 <= ord(key) <= 126:
            if len(command) < 40:
                command += key


def _draw_ready(term: Terminal, command: str,
                message: str, profile: dict):
    """Draw the READY prompt screen."""
    term.clear()
    term.put(0, 0, "=" * 80, ATTR_REVERSE)
    term.put(0, 2, " PY360 - TSO READY ", ATTR_REVERSE)

    term.put(2, 0, "-" * 80, ATTR_DIM)
    term.put(4, 3, "READY", ATTR_BOLD)
    term.put(5, 3, f"===> {command}", ATTR_NORMAL)

    term.put(8,  3, "Available commands:", ATTR_DIM)
    term.put(9,  5, "LOGON    - Log on to PY360", ATTR_DIM)
    term.put(10, 5, "APPLS    - Return to ISPF menu", ATTR_DIM)
    term.put(11, 5, "SHUTDOWN - Shutdown PY360 system", ATTR_DIM)
    term.put(12, 5, "LOGOFF   - (already at READY)", ATTR_DIM)

    if message:
        term.put(14, 3, message, ATTR_BOLD)

    term.move_cursor(5, 8 + len(command))
    term.refresh()


# -------------------------------------------------------------------
# MAIN BOOT LOOP
# -------------------------------------------------------------------

def main():

    # --- Phase 1: Boot prompt ---
    ipl_addr = boot_prompt()

    # --- Phase 2: IPL Sequence (plain text console) ---
    config.run_ipl()

    # --- Phase 3: Terminal Window opens ---
    term = Terminal(sysname=config.sysname())
    profile = None

    # Main session loop
    while True:

        # --- Phase 4: Login ---
        profile = logo.show(term)

        if profile is None:
            # ESC at login - drop to READY with no user
            profile = {}

        else:
            # --- Phase 5: ISPF Menu ---
            import menu
            menu.show(term, profile)

        # --- Phase 6: READY prompt ---
        while True:
            action = ready_prompt(term, profile)

            if action == "logon":
                break  # break inner loop, go back to login

            elif action == "appls":
                if profile:
                    import menu
                    menu.show(term, profile)
                    # After menu X, back to READY
                    continue
                else:
                    continue

            elif action == "shutdown":
                shutdown(term)
                return  # exit main()

    # Clean exit
    print("\nPY360 session ended.")


if __name__ == "__main__":
    main()