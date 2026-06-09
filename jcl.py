"""
jcl.py - PY360 JCL Interpreter
Part of the Python Mainframe Experience Layer

Implements a subset of IBM Job Control Language sufficient
for submitting and running REXX programs in batch mode.

Supported statements:
    //jobname  JOB  (acct),'name',CLASS=x,MSGCLASS=x
    //stepname EXEC PGM=REXXRUN
    //ddname   DD   DSN=dataset,DISP=SHR|OLD|NEW
    //ddname   DD   SYSOUT=*
    //* comment lines

Supported PGMs:
    REXXRUN   - Execute a REXX program
    IEFBR14   - IBM null program
"""

import os
import sys
import re
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import catalog
import spool

SIM_ROOT = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------------------------
# JCL ERROR
# -------------------------------------------------------------------

class JCLError(Exception):
    pass


# -------------------------------------------------------------------
# JCL STATEMENT
# -------------------------------------------------------------------

class JCLStatement:
    """Represents a single parsed JCL statement."""
    def __init__(self, name: str, stype: str, params: dict, raw: str):
        self.name   = name
        self.stype  = stype
        self.params = params
        self.raw    = raw


# -------------------------------------------------------------------
# JCL PARSER
# -------------------------------------------------------------------

class JCLParser:
    """Parses JCL source lines into JCLStatement objects."""

    def parse(self, lines: list) -> list:
        stmts    = []
        combined = self._join_continuations(lines)
        for line in combined:
            stmt = self._parse_line(line)
            if stmt:
                stmts.append(stmt)
        return stmts

    def _join_continuations(self, lines: list) -> list:
        result  = []
        current = ""
        for line in lines:
            line = line.rstrip()
            if not line.strip():
                continue
            if current and line.startswith("//") and len(current) >= 72 and current[71] != " ":
                current = current.rstrip() + line[2:].strip()
            else:
                if current:
                    result.append(current)
                current = line
        if current:
            result.append(current)
        return result

    def _parse_line(self, line: str) -> JCLStatement | None:
        if not line.startswith("//"):
            return None
        if line.startswith("//*"):
            return JCLStatement("*", "COMMENT", {}, line)

        rest  = line[2:]
        parts = rest.split(None, 2)
        if not parts:
            return None

        name    = parts[0] if parts else ""
        stype   = parts[1].upper() if len(parts) > 1 else ""
        operand = parts[2] if len(parts) > 2 else ""
        operand = self._strip_inline_comment(operand)
        params  = self._parse_params(operand)

        return JCLStatement(name, stype, params, line)

    def _strip_inline_comment(self, operand: str) -> str:
        in_quote = False
        quote    = ""
        i        = 0
        while i < len(operand) - 1:
            ch = operand[i]
            if not in_quote and ch in ("'", '"'):
                in_quote = True
                quote    = ch
            elif in_quote and ch == quote:
                in_quote = False
            elif not in_quote and operand[i:i+2] == "  ":
                return operand[:i]
            i += 1
        return operand

    def _parse_params(self, operand: str) -> dict:
        params     = {}
        positional = []

        if not operand.strip():
            return params

        tokens = self._split_operand(operand)
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if "=" in token:
                k, v = token.split("=", 1)
                params[k.strip().upper()] = v.strip().strip("'\"")
            else:
                positional.append(token.strip("'\"()"))

        if positional:
            params["_positional"] = positional

        return params

    def _split_operand(self, operand: str) -> list:
        tokens   = []
        current  = ""
        depth    = 0
        in_quote = False
        quote    = ""

        for ch in operand:
            if not in_quote and ch in ("'", '"'):
                in_quote = True
                quote    = ch
                current += ch
            elif in_quote and ch == quote:
                in_quote = False
                current += ch
            elif not in_quote and ch == "(":
                depth   += 1
                current += ch
            elif not in_quote and ch == ")":
                depth   -= 1
                current += ch
            elif not in_quote and ch == "," and depth == 0:
                tokens.append(current)
                current = ""
            else:
                current += ch

        if current:
            tokens.append(current)

        return tokens


# -------------------------------------------------------------------
# JCL EXECUTOR
# -------------------------------------------------------------------

class JCLExecutor:
    def __init__(self, stmts: list, term=None):
        self.stmts   = stmts
        self.term    = term
        self.job_log = []
        self.rc      = 0

    def _log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.job_log.append(f"{ts} {msg}")

    def execute(self) -> tuple:
        job_stmt = next((s for s in self.stmts if s.stype == "JOB"), None)
        if not job_stmt:
            return (8, ["JCL ERROR: No JOB statement found"])

        job_name = job_stmt.name
        pos      = job_stmt.params.get("_positional", [])
        cls      = job_stmt.params.get("CLASS", "A")
        msgclass = job_stmt.params.get("MSGCLASS", "A")

        self._log(f"JES2  JOB {job_name} RECEIVED")
        self._log(f"JES2  CLASS={cls} MSGCLASS={msgclass}")
        self._log(f"JES2  JOB {job_name} STARTED")

        steps = self._build_steps()
        if not steps:
            self._log("JCL ERROR: No EXEC statement found")
            return (8, self.job_log)

        for step_name, pgm, dds in steps:
            self._log(f"IEF236I {job_name} - {step_name} - STEP WAS EXECUTED")
            rc = self._execute_step(job_name, step_name, pgm, dds)
            self._log(f"IEF142I {job_name}.{step_name} - STEP ENDED - COND CODE {rc:04d}")
            self.rc = max(self.rc, rc)
            if self.rc >= 8:
                self._log(f"IEF272I {job_name} - STEP {step_name} ABENDED - RC={rc}")
                break

        self._log(f"JES2  JOB {job_name} ENDED - MAX RC={self.rc}")
        spool.write_to_printer(self.job_log, job_name=f"{job_name}/JESLOG")

        return (self.rc, self.job_log)

    def _build_steps(self) -> list:
        steps        = []
        current_step = None
        current_dds  = {}

        for stmt in self.stmts:
            if stmt.stype == "EXEC":
                if current_step:
                    steps.append((current_step[0], current_step[1], current_dds))
                pgm          = stmt.params.get("PGM", "")
                current_step = (stmt.name, pgm)
                current_dds  = {}
            elif stmt.stype == "DD" and current_step:
                current_dds[stmt.name.upper()] = stmt.params

        if current_step:
            steps.append((current_step[0], current_step[1], current_dds))

        return steps

    def _execute_step(self, job_name: str, step_name: str,
                      pgm: str, dds: dict) -> int:
        pgm = pgm.upper()
        self._log(f"IEF233I {job_name}.{step_name} - EXEC PGM={pgm}")

        if pgm == "REXXRUN":
            return self._run_rexx(job_name, step_name, dds)
        elif pgm == "IEFBR14":
            self._log("IEF234I IEFBR14 - NULL STEP EXECUTED")
            return 0
        elif pgm == "SORT":
            self._log("IEF234I SORT - NOT YET IMPLEMENTED")
            return 4
        else:
            self._log(f"IEF450I {pgm} - PROGRAM NOT FOUND IN PY360")
            return 8

    def _run_rexx(self, job_name: str, step_name: str, dds: dict) -> int:
        sysin_dd = dds.get("SYSIN")
        if not sysin_dd:
            self._log("JCL ERROR: SYSIN DD NOT FOUND")
            return 8

        dsn = sysin_dd.get("DSN", "")
        if not dsn:
            self._log("JCL ERROR: SYSIN DD HAS NO DSN")
            return 8

        path = catalog.resolve_path(dsn)
        if not path:
            self._log(f"JCL ERROR: DSN NOT IN CATALOG: {dsn}")
            return 8

        if not os.path.exists(path):
            self._log(f"JCL ERROR: FILE NOT FOUND: {path}")
            return 8

        self._log(f"IEF237I {dsn} - SYSIN ALLOCATED")

        import rexx as py360rexx
        rc, output = py360rexx.run_batch(path, spool_path=spool.PRINTER_FILE)

        self._log(f"REXX  EXECUTION COMPLETE - {len(output)} LINES OUTPUT")
        self._log(f"REXX  RETURN CODE: {rc}")

        spool.write_to_printer(output, job_name=f"{job_name}.{step_name}")

        return rc


# -------------------------------------------------------------------
# PUBLIC ENTRY POINTS
# -------------------------------------------------------------------

def submit(jcl_path: str, term=None) -> tuple:
    """Submit a JCL job from a file path."""
    if not os.path.exists(jcl_path):
        return (8, [f"JCL ERROR: File not found: {jcl_path}"])

    with open(jcl_path, "r") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]

    try:
        parser   = JCLParser()
        stmts    = parser.parse(lines)
        executor = JCLExecutor(stmts, term=term)
        return executor.execute()
    except JCLError as e:
        return (8, [f"JCL ERROR: {e}"])
    except Exception as e:
        return (12, [f"SYSTEM ERROR: {e}"])


def submit_dsn(dsn: str, term=None) -> tuple:
    """Submit a JCL job from a catalog DSN."""
    path = catalog.resolve_path(dsn)
    if not path:
        return (8, [f"JCL ERROR: DSN NOT IN CATALOG: {dsn}"])
    return submit(path, term=term)


# -------------------------------------------------------------------
# SELF TEST
# -------------------------------------------------------------------

if __name__ == "__main__":
    config.load()

    print(f"SIM_ROOT    : {SIM_ROOT}")
    print(f"Catalog file: {catalog.CATALOG_FILE}")

    test_rexx = """\
/* Test REXX program for JCL batch execution */
SAY "Hello from JCL batch job!"
SAY "Date:" DATE()
SAY "Time:" TIME()
DO I = 1 TO 3
  SAY "Batch line" I
END
SAY "Job complete."
EXIT 0
"""

    test_jcl = """\
//TESTJOB  JOB (001),'DAVE',CLASS=A,MSGCLASS=A
//* Test JCL job
//STEP1    EXEC PGM=REXXRUN
//SYSIN    DD DSN=USER.DAVE.BATCHTST,DISP=SHR
//SYSOUT   DD SYSOUT=*
"""

    # Allocate and write REXX dataset
    rexx_dsn = "USER.DAVE.BATCHTST"
    if not catalog.exists(rexx_dsn):
        ok = catalog.allocate(rexx_dsn, description="JCL batch test")
        print(f"Allocated {rexx_dsn}: {ok}")
    else:
        print(f"{rexx_dsn} already exists")

    rexx_path = catalog.resolve_path(rexx_dsn)
    print(f"REXX path   : {rexx_path}")
    if not rexx_path:
        print("ERROR: Could not resolve REXX dataset - check catalog")
        sys.exit(1)
    with open(rexx_path, "w") as f:
        f.write(test_rexx)
    print(f"REXX written: {rexx_path}")

    # Allocate and write JCL dataset
    jcl_dsn = "USER.DAVE.TESTJCL"
    if not catalog.exists(jcl_dsn):
        ok = catalog.allocate(jcl_dsn, description="Test JCL job")
        print(f"Allocated {jcl_dsn}: {ok}")
    else:
        print(f"{jcl_dsn} already exists")

    jcl_path = catalog.resolve_path(jcl_dsn)
    print(f"JCL path    : {jcl_path}")
    if not jcl_path:
        print("ERROR: Could not resolve JCL dataset - check catalog")
        sys.exit(1)
    with open(jcl_path, "w") as f:
        f.write(test_jcl)
    print(f"JCL written : {jcl_path}")

    print("\n=== Submitting JCL job ===\n")
    rc, log = submit(jcl_path)

    print("=== JOB LOG ===")
    for line in log:
        print(line)
    print(f"\nJob RC: {rc}")
    print("\nCheck spool\\printout.txt for output.")