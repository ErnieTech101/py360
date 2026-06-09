"""
help.py - PY360 HELP System
Part of the Python Mainframe Experience Layer

Displays context-sensitive help screens using the browse engine.
    Help text files live in the help\\ directory under SIM_ROOT.

Usage:
    import help as py360help
    py360help.show("MENU", term)
    py360help.show("EDITOR", term)
    py360help.show("BROWSE", term)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import browse
from terminal import Terminal

HELP_DIR = os.path.join(config.SIM_ROOT, "help")

# Map of topic names to help file names
HELP_TOPICS = {
    "MAIN":     "main.txt",
    "MENU":     "menu.txt",
    "EDITOR":   "editor.txt",
    "BROWSE":   "browse.txt",
    "UTIL":     "util.txt",
    "CATALOG":  "catalog.txt",
    "JCL":      "jcl.txt",
    "BASIC":    "basic.txt",
    "SPOOL":    "spool.txt",
    "LOGIN":    "login.txt",
    "GLOSSARY": "glossary.txt",
    "REXX":     "rexx.txt",
}


def show(topic: str, term: Terminal):
    """
    Display help for the given topic.
    Falls back to main help if topic not found.
    """
    topic = topic.upper().strip()
    filename = HELP_TOPICS.get(topic, "main.txt")
    path     = os.path.join(HELP_DIR, filename)

    if not os.path.exists(path):
        # Show a basic not-found message
        lines = [
            f"HELP - {topic}",
            "=" * 60,
            "",
            f"No help available for topic: {topic}",
            "",
            "Available help topics:",
            "",
        ] + [f"  {k:<12} - {v}" for k, v in HELP_TOPICS.items()] + [
            "",
            "Type HELP <topic> at any COMMAND ===> prompt.",
        ]
        browse.browse_lines(lines, f"HELP - {topic}", term)
        return

    browse.browse_file(path, term, title=f"HELP - {topic}")


def _write_help_files():
    """
    Create the help directory and default help text files.
    Called once at setup or if help files are missing.
    """
    os.makedirs(HELP_DIR, exist_ok=True)

    files = {}

    # --- MAIN ---
    files["main.txt"] = """\
PY360 - HELP SYSTEM
===================

Welcome to PY360 - Python/360 MVS OS Mainframe Simulator.

PY360 simulates the look and feel of an IBM MVS mainframe
environment running on Windows 10/11.

AVAILABLE HELP TOPICS
---------------------
  MENU      Primary option menu navigation
  EDITOR    ISPF-style editor commands
  BROWSE    Dataset browser commands
  UTIL      Dataset utility functions
  CATALOG   Dataset catalog management
  JCL       Job Control Language basics
  REXX      PY360 REXX interpreter
  BASIC     PY360 BASIC interpreter
  SPOOL     Spool and job output viewer
  LOGIN     Login and user profile
  GLOSSARY  Mainframe concept glossary

To display help for a specific topic, type:
  HELP <topic>
at any COMMAND ===> prompt, or press F1 from any screen.

GENERAL NAVIGATION
------------------
  F1        Display context-sensitive help
  F3        Exit current screen / save if modified
  F4        Exit without saving
  F7        Scroll up (Page Up)
  F8        Scroll down (Page Down)
  TAB       Move between fields
  ENTER     Execute command
"""

    # --- MENU ---
    files["menu.txt"] = """\
PY360 - PRIMARY OPTION MENU HELP
=================================

The Primary Option Menu is the main entry point for all
PY360 functions. Type an option number and press ENTER.

MENU OPTIONS
------------
  1  BROWSE     Display a dataset in read-only mode
  2  EDIT       Create or modify a dataset
  3  UTILITIES  Dataset management functions
  4  FOREGROUND Run a PY360 BASIC program
  5  BATCH      Submit a job via JCL
  6  SPOOL      View job output and spool files
  7  STATUS     Display system status
  X  LOGOFF     End your PY360 session

NAVIGATION
----------
  Type the option number at OPTION ===> and press ENTER.
  Press F3 or type X to logoff.
  Press F1 for help on any screen.

COMMAND SHORTCUTS
-----------------
  You may also type full commands at the OPTION prompt:
  LOGOFF    End session
  HELP      Display this help screen
"""

    # --- EDITOR ---
    files["editor.txt"] = """\
PY360 - EDITOR HELP
====================

The PY360 editor provides ISPF-style full screen editing.

SCREEN LAYOUT
-------------
  Row 1   : Title bar - dataset name and position
  Row 2   : COMMAND ===> field for primary commands
  Row 3   : TOP OF DATA marker
  Rows 4+ : Data lines with line numbers
  Last row: BOTTOM OF DATA marker
  OIA     : Status line at very bottom

NAVIGATION
----------
  TAB       Cycle between COMMAND, line number, and text areas
  Arrow keys Move cursor
  PgUp/F7   Scroll up one page
  PgDn/F8   Scroll down one page
  F3        Save and exit
  F4        Exit without saving

PRIMARY COMMANDS (type at COMMAND ===> then ENTER)
--------------------------------------------------
  SAVE      Save the file
  CANCEL    Exit without saving
  END       Save and exit
  FIND str  Find string (case insensitive)
  CHANGE s1 s2  Change first occurrence of s1 to s2
  UP n      Scroll up n lines
  DOWN n    Scroll down n lines

LINE COMMANDS (type in line number area then ENTER)
---------------------------------------------------
  D         Delete line
  I         Insert blank line below
  R         Repeat line
  C         Copy line (then use A or B to paste)
  M         Move line (then use A or B to paste)
  A         Paste after this line
  B         Paste before this line
  CC...CC   Copy block of lines
  MM...MM   Move block of lines
"""

    # --- BROWSE ---
    files["browse.txt"] = """\
PY360 - BROWSE HELP
====================

BROWSE displays a dataset or file in read-only mode.
No changes can be made to the file while browsing.

SCREEN LAYOUT
-------------
  Row 1   : Title bar - dataset name and line position
  Row 2   : COMMAND ===> field
  Row 3   : TOP OF DATA marker
  Rows 4+ : Data lines with line numbers
  Last row: Message and key reminder line

NAVIGATION
----------
  F3 / ESC  Exit browse
  F7 / PgUp Scroll up one page
  F8 / PgDn Scroll down one page
  Up/Down   Scroll one line at a time

PRIMARY COMMANDS (type at COMMAND ===> then ENTER)
--------------------------------------------------
  TOP       Jump to top of file
  BOTTOM    Jump to bottom of file
  FIND str  Search for string (wraps around)
  UP n      Scroll up n lines
  DOWN n    Scroll down n lines
  END       Exit browse
"""

    # --- UTIL ---
    files["util.txt"] = """\
PY360 - UTILITIES HELP
=======================

Dataset utility functions allow you to manage your
PY360 datasets from within the system.

AVAILABLE UTILITIES
-------------------
  1  LISTCAT    List all datasets in catalog
  2  ALLOCATE   Create a new dataset
  3  DELETE     Delete an existing dataset
  4  RENAME     Rename a dataset
  5  COPY       Copy one dataset to another
  6  LISTDS     Display dataset details

DATASET NAMING RULES
--------------------
  Datasets follow IBM DSN conventions:
  - Maximum 44 characters total
  - Dot-separated qualifiers
  - Each qualifier 1-8 characters
  - Must start with a letter
  - Example: USER.DAVE.SOURCE

DEFAULT PREFIX
--------------
  Your default prefix is set in your user profile.
  LISTCAT will filter by your prefix automatically.
"""

    # --- CATALOG ---
    files["catalog.txt"] = """\
PY360 - CATALOG HELP
=====================

The PY360 catalog tracks all allocated datasets.
It is stored as catalog.json in the PY360 root directory.

CATALOG ENTRIES
---------------
  Each dataset entry contains:
    DSN      Dataset name
    PATH     Physical file location
    RECFM    Record format (FB, F, V, VB)
    LRECL    Logical record length
    CREATED  Creation date
    DESC     Description

RECFM VALUES
------------
  FB   Fixed Block (most common, default)
  F    Fixed Unblocked
  V    Variable
  VB   Variable Block

LRECL
-----
  Logical record length in bytes.
  Default is 80 (standard mainframe card image).
"""

    # --- JCL ---
    files["jcl.txt"] = """\
PY360 - JCL HELP
=================

PY360 supports a simplified subset of IBM Job Control
Language (JCL) for batch job submission.

JCL STATEMENT TYPES
-------------------
  JOB     Identifies the job and its attributes
  EXEC    Specifies the program to execute
  DD      Defines data sets used by the program

BASIC JCL EXAMPLE
-----------------
  //MYJOB   JOB (ACCT),'YOUR NAME',CLASS=A
  //STEP1   EXEC PGM=BASICRUN
  //INPUT   DD DSN=USER.DAVE.MYPROG,DISP=SHR
  //OUTPUT  DD DSN=USER.DAVE.OUTPUT,DISP=NEW
  //SYSOUT  DD SYSOUT=*

JOB STATEMENT
-------------
  //jobname JOB (account),'programmer name',CLASS=x

EXEC STATEMENT
--------------
  //stepname EXEC PGM=programname

DD STATEMENT
------------
  //ddname DD DSN=dataset.name,DISP=disposition
  DISP values: SHR, OLD, NEW, MOD

SYSOUT
------
  //ddname DD SYSOUT=*
  Routes output to the PY360 spool file.
"""

    # --- BASIC ---
    files["basic.txt"] = """\
PY360 - BASIC INTERPRETER HELP
================================

PY360 BASIC is a line-numbered BASIC interpreter
built into PY360 for writing and running simple programs.

PROGRAM STRUCTURE
-----------------
  Programs consist of numbered lines.
  Line numbers must be in ascending order.
  Example:
    10 REM My first PY360 BASIC program
    20 PRINT "Hello from PY360!"
    30 END

KEYWORDS
--------
  LET       Assign a value:  LET X = 10
  PRINT     Display output:  PRINT "Hello"
  INPUT     Get user input:  INPUT X
  IF/THEN   Conditional:     IF X > 10 THEN GOTO 100
  GOTO      Jump to line:    GOTO 200
  GOSUB     Call subroutine: GOSUB 500
  RETURN    Return from sub: RETURN
  FOR/NEXT  Loop:            FOR I = 1 TO 10
  REM       Comment:         REM This is a comment
  END       End program:     END
  STOP      Stop execution:  STOP
  PRINT     Print to spool:  PRINT #1, "text"

RUNNING A PROGRAM
-----------------
  From the menu select option 4 FOREGROUND
  Enter the dataset name containing your BASIC program.
  Output goes to the PY360 spool viewer.
"""

    # --- SPOOL ---
    files["spool.txt"] = """\
PY360 - SPOOL VIEWER HELP
==========================

The spool viewer displays output from batch jobs
and BASIC programs run in foreground mode.

SPOOL FILES
-----------
  PRT001  Main printer output  (spool\\printout.txt)
  PCH001  Card punch output    (spool\\punch.txt)

NAVIGATION
----------
  F3 / ESC  Exit spool viewer
  F7 / PgUp Scroll up
  F8 / PgDn Scroll down
  FIND str  Search for string

COMMANDS
--------
  TOP       Jump to top of spool
  BOTTOM    Jump to bottom of spool
  PURGE     Clear the spool file
  PRINT     Send spool to printer
"""

    # --- LOGIN ---
    files["login.txt"] = """\
PY360 - LOGIN HELP
===================

The PY360 login screen authenticates users and
loads their personal profile settings.

LOGIN PROCEDURE
---------------
  1. Type your USERID and press TAB or ENTER
  2. Type your PASSWORD and press ENTER
  3. Your profile will be loaded automatically

NEW USERS
---------
  If your USERID is not found in the system,
  a new profile will be created automatically
  with default settings.

USER PROFILE
------------
  Your profile is stored as:
    users\\userid.json

  Profile contains:
    USERID      Your user identifier
    PREFIX      Default dataset prefix
    LASTLOGIN   Last login timestamp
    LRECL       Default record length
    RECFM       Default record format
    SCROLLMODE  Default scroll mode

PASSWORD
--------
  Passwords are not validated in PY360.
  This is a single-user simulation system.
  Any password will be accepted.
"""

    # Write all files
    for filename, content in files.items():
        filepath = os.path.join(HELP_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(content)
            print(f"HELP: Created {filename}")


# --- Self Test ---
if __name__ == "__main__":
    config.load()
    _write_help_files()
    print("Help files created successfully.")

    from terminal import Terminal
    term = Terminal(sysname=config.sysname())
    show("MAIN", term)
    term.close()