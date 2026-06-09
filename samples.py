"""
samples.py - PY360 Sample Library
Part of the Python Mainframe Experience Layer

Creates and populates the SYS.REXX and SYS.JCL sample
libraries during IPL. Safe to call multiple times -
only creates datasets that don't already exist.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import catalog

# -------------------------------------------------------------------
# REXX SAMPLES
# -------------------------------------------------------------------

REXX_SAMPLES = {}

REXX_SAMPLES["SYS.REXX.HELLO"] = (
    "Classic Hello World program",
"""\
/* SYS.REXX.HELLO - Hello World */
/* PY360 Sample REXX Program    */

SAY "Hello from PY360 REXX!"
SAY ""
SAY "Welcome to the Python/360 Mainframe Simulator."
SAY "This is a classic Hello World program."
SAY ""
SAY "Date:" DATE()
SAY "Time:" TIME()
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.CALC"] = (
    "Simple calculator demonstration",
"""\
/* SYS.REXX.CALC - Calculator Demo */
/* PY360 Sample REXX Program       */

SAY "PY360 REXX Calculator Demo"
SAY COPIES("=", 40)
SAY ""

A = 100
B = 7

SAY "A =" A
SAY "B =" B
SAY ""
SAY "Addition      : A + B =" A + B
SAY "Subtraction   : A - B =" A - B
SAY "Multiplication: A * B =" A * B
SAY "Division      : A / B =" A / B
SAY "Integer Div   : A // B =" A // B
SAY "Modulus       : A  % B =" A  % B
SAY "Power         : A ** 2 =" A ** 2
SAY ""
SAY "Square root of A:" FORMAT(A ** 0.5, 6, 4)
SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.SYSINFO"] = (
    "Display PY360 system information",
"""\
/* SYS.REXX.SYSINFO - System Information */
/* PY360 Sample REXX Program             */

SAY "PY360 System Information Report"
SAY COPIES("=", 40)
SAY ""
SAY "Report Date :" DATE()
SAY "Report Time :" TIME()
SAY ""
SAY "REXX Functions Available:"
SAY COPIES("-", 30)

/* String functions */
SAY "  LENGTH   : LENGTH('HELLO') =" LENGTH("HELLO")
SAY "  UPPER    : UPPER('hello') =" UPPER("hello")
SAY "  LOWER    : LOWER('WORLD') =" LOWER("WORLD")
SAY "  REVERSE  : REVERSE('PY360') =" REVERSE("PY360")
SAY "  COPIES   : COPIES('AB',4) =" COPIES("AB", 4)
SAY "  SUBSTR   : SUBSTR('MAINFRAME',5,5) =" SUBSTR("MAINFRAME", 5, 5)
SAY "  WORDS    : WORDS('ONE TWO THREE') =" WORDS("ONE TWO THREE")
SAY "  WORD     : WORD('ONE TWO THREE',2) =" WORD("ONE TWO THREE", 2)
SAY ""
SAY "Math Functions:"
SAY COPIES("-", 30)
SAY "  ABS(-42)  =" ABS(-42)
SAY "  MAX(3,7,2)=" MAX(3, 7, 2)
SAY "  MIN(3,7,2)=" MIN(3, 7, 2)
SAY "  SIGN(-5)  =" SIGN(-5)
SAY "  TRUNC(3.7)=" TRUNC(3.7)
SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.LOOPS"] = (
    "Loop examples DO WHILE UNTIL FOREVER",
"""\
/* SYS.REXX.LOOPS - Loop Examples */
/* PY360 Sample REXX Program      */

SAY "PY360 REXX Loop Examples"
SAY COPIES("=", 40)
SAY ""

/* Simple counted loop */
SAY "Counted Loop - DO I = 1 TO 5:"
DO I = 1 TO 5
  SAY "  Iteration" I
END
SAY ""

/* Counted loop with step */
SAY "Counted Loop with BY 2 - DO I = 0 TO 10 BY 2:"
DO I = 0 TO 10 BY 2
  SAY "  I =" I
END
SAY ""

/* DO WHILE */
SAY "DO WHILE loop:"
N = 1
DO WHILE N <= 4
  SAY "  N =" N
  N = N + 1
END
SAY ""

/* DO UNTIL */
SAY "DO UNTIL loop:"
X = 10
DO UNTIL X <= 0
  SAY "  X =" X
  X = X - 3
END
SAY ""

/* Nested loops */
SAY "Nested loops - multiplication table (1-3):"
DO R = 1 TO 3
  DO C = 1 TO 3
    SAY "  " R "x" C "=" R * C
  END
END
SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.STRFUNC"] = (
    "String function demonstrations",
"""\
/* SYS.REXX.STRFUNC - String Functions */
/* PY360 Sample REXX Program           */

SAY "PY360 REXX String Function Demos"
SAY COPIES("=", 40)
SAY ""

S = "Hello from PY360 REXX!"

SAY "Source string: '" || S || "'"
SAY ""
SAY "LENGTH(S)          =" LENGTH(S)
SAY "UPPER(S)           =" UPPER(S)
SAY "LOWER(S)           =" LOWER(S)
SAY "REVERSE(S)         =" REVERSE(S)
SAY "SUBSTR(S,1,5)      =" SUBSTR(S, 1, 5)
SAY "SUBSTR(S,12,5)     =" SUBSTR(S, 12, 5)
SAY "LEFT(S,5)          =" LEFT(S, 5)
SAY "RIGHT(S,5)         =" RIGHT(S, 5)
SAY "CENTER('PY360',20) =" CENTER("PY360", 20)
SAY "WORDS(S)           =" WORDS(S)
SAY "WORD(S,3)          =" WORD(S, 3)
SAY "POS('PY360',S)     =" POS("PY360", S)
SAY "STRIP('  hello  ') =" STRIP("  hello  ")
SAY "COPIES('=-',10)    =" COPIES("=-", 10)
SAY ""

/* String concatenation */
FIRST = "MAIN"
LAST  = "FRAME"
SAY "Concatenation with ||:"
SAY "  FIRST || LAST =" FIRST || LAST
SAY ""
SAY "Implicit concatenation:"
SAY "  FIRST LAST =" FIRST LAST
SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.FIBONACI"] = (
    "Fibonacci sequence generator",
"""\
/* SYS.REXX.FIBONACI - Fibonacci Sequence */
/* PY360 Sample REXX Program              */

SAY "PY360 REXX - Fibonacci Sequence"
SAY COPIES("=", 40)
SAY ""
SAY "First 15 Fibonacci numbers:"
SAY ""

A = 0
B = 1
DO I = 1 TO 15
  SAY "  F(" || I || ") =" A
  C = A + B
  A = B
  B = C
END

SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.PRIMES"] = (
    "Prime number generator",
"""\
/* SYS.REXX.PRIMES - Prime Number Generator */
/* PY360 Sample REXX Program                */

SAY "PY360 REXX - Prime Numbers up to 50"
SAY COPIES("=", 40)
SAY ""

COUNT = 0
DO N = 2 TO 50
  PRIME = 1
  DO D = 2 TO TRUNC(N ** 0.5)
    IF N // D = 0 THEN
      PRIME = 0
  END
  IF PRIME = 1 THEN DO
    SAY "  Prime:" N
    COUNT = COUNT + 1
  END
END

SAY ""
SAY "Total primes found:" COUNT
SAY COPIES("=", 40)
EXIT 0
"""
)

REXX_SAMPLES["SYS.REXX.DATEUTIL"] = (
    "Date and time utilities",
"""\
/* SYS.REXX.DATEUTIL - Date and Time Utilities */
/* PY360 Sample REXX Program                   */

SAY "PY360 REXX Date and Time Utilities"
SAY COPIES("=", 40)
SAY ""

SAY "Current date and time:"
SAY COPIES("-", 30)
SAY "  Normal   : " DATE()
SAY "  Sorted   : " DATE("S")
SAY "  US format: " DATE("U")
SAY "  European : " DATE("E")
SAY ""
SAY "  Time     : " TIME()
SAY "  Hour     : " TIME("H")
SAY "  Seconds  : " TIME("S")
SAY ""

/* Day of week calculation */
SAY "Date arithmetic:"
SAY COPIES("-", 30)
TODAY = DATE("S")
SAY "  Today (YYYYMMDD):" TODAY
YEAR  = SUBSTR(TODAY, 1, 4)
MONTH = SUBSTR(TODAY, 5, 2)
DAY   = SUBSTR(TODAY, 7, 2)
SAY "  Year :" YEAR
SAY "  Month:" MONTH
SAY "  Day  :" DAY
SAY ""
SAY COPIES("=", 40)
EXIT 0
"""
)


# -------------------------------------------------------------------
# JCL SAMPLES
# -------------------------------------------------------------------

JCL_SAMPLES = {}

JCL_SAMPLES["SYS.JCL.HELLO"] = (
    "Simple Hello World batch job",
"""\
//HELLO    JOB (SYS),'SAMPLE JOB',CLASS=A,MSGCLASS=A
//*
//* SYS.JCL.HELLO - Hello World Batch Job
//* Runs the SYS.REXX.HELLO program in batch mode
//*
//STEP1    EXEC PGM=REXXRUN
//SYSIN    DD DSN=SYS.REXX.HELLO,DISP=SHR
//SYSOUT   DD SYSOUT=*
"""
)

JCL_SAMPLES["SYS.JCL.RUNJOB"] = (
    "Template JCL for running REXX programs",
"""\
//RUNJOB   JOB (ACCT),'YOUR NAME',CLASS=A,MSGCLASS=A
//*
//* SYS.JCL.RUNJOB - Template JCL for REXX programs
//*
//* Instructions:
//*   1. Copy this JCL to your own dataset
//*      e.g. USER.yourname.MYJCL
//*   2. Change MYJOB to your job name
//*   3. Change USER.yourname.MYPROG to your REXX dataset
//*   4. Submit from menu option 5 BATCH
//*
//STEP1    EXEC PGM=REXXRUN
//SYSIN    DD DSN=USER.DAVE.HELLO,DISP=SHR
//SYSOUT   DD SYSOUT=*
"""
)

JCL_SAMPLES["SYS.JCL.IEFBR14"] = (
    "Null job example using IEFBR14",
"""\
//NULLJOB  JOB (SYS),'NULL JOB',CLASS=A,MSGCLASS=A
//*
//* SYS.JCL.IEFBR14 - The classic IBM null program
//*
//* IEFBR14 is a famous IBM utility program that does
//* absolutely nothing. It is used to:
//*   - Test JCL syntax
//*   - Allocate or delete datasets via DD statements
//*   - Serve as a placeholder step
//*
//* On real MVS systems IEFBR14 consists of just two
//* instructions: BALR 14,0 and BR 14 (branch back).
//*
//STEP1    EXEC PGM=IEFBR14
//SYSOUT   DD SYSOUT=*
"""
)

JCL_SAMPLES["SYS.JCL.MULTJOB"] = (
    "Multi-step job example",
"""\
//MULTJOB  JOB (SYS),'MULTI STEP',CLASS=A,MSGCLASS=A
//*
//* SYS.JCL.MULTJOB - Multi-step job example
//*
//* This job demonstrates multiple steps in a single job.
//* Each step runs a different REXX program.
//* Steps execute in order. If a step fails (RC>=8)
//* subsequent steps may be skipped.
//*
//STEP1    EXEC PGM=REXXRUN
//* Step 1 - Run Hello World
//SYSIN    DD DSN=SYS.REXX.HELLO,DISP=SHR
//SYSOUT   DD SYSOUT=*
//*
//STEP2    EXEC PGM=REXXRUN
//* Step 2 - Run Calculator demo
//SYSIN    DD DSN=SYS.REXX.CALC,DISP=SHR
//SYSOUT   DD SYSOUT=*
//*
//STEP3    EXEC PGM=IEFBR14
//* Step 3 - Null step
//SYSOUT   DD SYSOUT=*
"""
)


# -------------------------------------------------------------------
# INSTALL FUNCTION
# -------------------------------------------------------------------

def install_samples(ipl_msg=None) -> int:
    """
    Allocate and populate all sample datasets.
    Called during IPL. Returns count of datasets created.
    Safe to call multiple times - skips existing datasets.

    ipl_msg: optional function(str) for IPL console output
    """
    created = 0

    def msg(text):
        if ipl_msg:
            ipl_msg(text)

    # Install REXX samples
    for dsn, (desc, content) in REXX_SAMPLES.items():
        if not catalog.exists(dsn):
            ok = catalog.allocate(dsn, recfm="FB", lrecl=80,
                                  description=desc)
            if ok:
                path = catalog.resolve_path(dsn)
                if path:
                    with open(path, "w") as f:
                        f.write(content)
                    created += 1
                    msg(f"SAMPLE LIBRARY: ALLOCATED {dsn}")

    # Install JCL samples
    for dsn, (desc, content) in JCL_SAMPLES.items():
        if not catalog.exists(dsn):
            ok = catalog.allocate(dsn, recfm="FB", lrecl=80,
                                  description=desc)
            if ok:
                path = catalog.resolve_path(dsn)
                if path:
                    with open(path, "w") as f:
                        f.write(content)
                    created += 1
                    msg(f"SAMPLE LIBRARY: ALLOCATED {dsn}")

    if created > 0:
        msg(f"SAMPLE LIBRARY: {created} DATASETS INSTALLED")
    else:
        msg("SAMPLE LIBRARY: ALL SAMPLES ALREADY INSTALLED")

    return created


# -------------------------------------------------------------------
# SELF TEST
# -------------------------------------------------------------------

if __name__ == "__main__":
    import config
    config.load()

    print("Installing sample library...\n")

    def print_msg(text):
        print(f"  {text}")

    count = install_samples(ipl_msg=print_msg)
    print(f"\nDone. {count} datasets created.")
    print("\nSample datasets:")
    for e in catalog.listcat("SYS."):
        print(f"  {e['dsn']:<30} {e['description']}")