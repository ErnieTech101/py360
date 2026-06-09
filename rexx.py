"""
rexx.py - PY360 REXX Interpreter
Part of the Python Mainframe Experience Layer

Implements a subset of IBM REXX sufficient for meaningful
mainframe-style programs.
"""

import os
import sys
import re
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# --- Token Types ---
TK_NUMBER  = "NUMBER"
TK_STRING  = "STRING"
TK_IDENT   = "IDENT"
TK_OP      = "OP"
TK_LPAREN  = "LPAREN"
TK_RPAREN  = "RPAREN"
TK_CONCAT  = "CONCAT"
TK_EOF     = "EOF"


class RexxError(Exception):
    pass


# -------------------------------------------------------------------
# LEXER
# -------------------------------------------------------------------

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos  = 0

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t":
            self.pos += 1

    def read_string(self) -> tuple:
        quote  = self.advance()
        result = ""
        while self.pos < len(self.text):
            ch = self.advance()
            if ch == quote:
                if self.pos < len(self.text) and self.text[self.pos] == quote:
                    result += quote
                    self.pos += 1
                else:
                    break
            else:
                result += ch
        return (TK_STRING, result)

    def read_number(self) -> tuple:
        start = self.pos - 1
        while self.pos < len(self.text) and self.text[self.pos] in "0123456789.":
            self.pos += 1
        return (TK_NUMBER, self.text[start:self.pos])

    def read_ident(self) -> tuple:
        start = self.pos - 1
        while self.pos < len(self.text) and (
                self.text[self.pos].isalnum() or self.text[self.pos] in "_!?@#$"):
            self.pos += 1
        return (TK_IDENT, self.text[start:self.pos])

    def tokenize(self) -> list:
        tokens = []
        while self.pos < len(self.text):
            self.skip_whitespace()
            if self.pos >= len(self.text):
                break
            ch = self.advance()

            if ch in ('"', "'"):
                self.pos -= 1
                tokens.append(self.read_string())
            elif ch.isdigit():
                tokens.append(self.read_number())
            elif ch.isalpha() or ch in "_!?@#$":
                tokens.append(self.read_ident())
            elif ch == "(":
                tokens.append((TK_LPAREN, "("))
            elif ch == ")":
                tokens.append((TK_RPAREN, ")"))
            elif ch == "|" and self.peek() == "|":
                self.advance()
                tokens.append((TK_CONCAT, "||"))
            elif ch in "+-*/<>=!&|%\\":
                op = ch
                if self.peek() in "=<>*":
                    op += self.advance()
                tokens.append((TK_OP, op))
            elif ch == ",":
                tokens.append((TK_OP, ","))

        tokens.append((TK_EOF, ""))
        return tokens


# -------------------------------------------------------------------
# EXPRESSION EVALUATOR
# -------------------------------------------------------------------

class Evaluator:
    def __init__(self, env: dict):
        self.env    = env
        self.tokens = []
        self.pos    = 0

    def peek_tok(self) -> tuple:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (TK_EOF, "")

    def next_tok(self) -> tuple:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def evaluate(self, expr: str) -> str:
        self.tokens = Lexer(expr).tokenize()
        self.pos    = 0
        result      = self._parse_expr()
        return str(result)

    def _parse_expr(self) -> str:
        left = self._parse_concat()
        while self.peek_tok()[0] == TK_OP and self.peek_tok()[1] in (
                "=", "\\=", "<", ">", "<=", ">=", "<>", "&", "|"):
            op    = self.next_tok()[1]
            right = self._parse_concat()
            left  = self._compare(left, op, right)
        return left

    def _parse_concat(self) -> str:
        left = self._parse_add()
        while self.peek_tok()[0] in (TK_STRING, TK_IDENT, TK_NUMBER):
            right = self._parse_add()
            left  = str(left) + " " + str(right)
        return left

    def _parse_add(self) -> str:
        left = self._parse_mul()
        while self.peek_tok()[0] == TK_OP and self.peek_tok()[1] in ("+", "-"):
            op    = self.next_tok()[1]
            right = self._parse_mul()
            left  = self._math(left, op, right)
        return left

    def _parse_mul(self) -> str:
        left = self._parse_power()
        while self.peek_tok()[0] == TK_OP and self.peek_tok()[1] in ("*", "/", "%", "//"):
            op    = self.next_tok()[1]
            right = self._parse_power()
            left  = self._math(left, op, right)
        return left

    def _parse_power(self) -> str:
        left = self._parse_unary()
        if self.peek_tok()[0] == TK_OP and self.peek_tok()[1] == "**":
            self.next_tok()
            right  = self._parse_unary()
            try:
                result = float(left) ** float(right)
                if result == int(result):
                    return str(int(result))
                return f"{result:.9g}"
            except Exception:
                raise RexxError(f"Invalid power: {left} ** {right}")
        return left

    def _parse_unary(self) -> str:
        if self.peek_tok()[0] == TK_OP and self.peek_tok()[1] == "-":
            self.next_tok()
            val = self._parse_primary()
            try:
                return str(-float(val))
            except Exception:
                raise RexxError(f"Cannot negate: {val}")
        return self._parse_primary()

    def _parse_primary(self) -> str:
        tok_type, tok_val = self.next_tok()

        if tok_type == TK_NUMBER:
            return tok_val
        elif tok_type == TK_STRING:
            return tok_val
        elif tok_type == TK_LPAREN:
            val = self._parse_expr()
            if self.peek_tok()[0] == TK_RPAREN:
                self.next_tok()
            return val
        elif tok_type == TK_IDENT:
            name = tok_val.upper()
            if self.peek_tok()[0] == TK_LPAREN:
                return self._call_builtin(name)
            return self.env.get(name, name)
        elif tok_type == TK_EOF:
            return ""
        return str(tok_val)

    def _call_builtin(self, name: str) -> str:
        self.next_tok()  # consume (
        args = []
        while self.peek_tok()[0] != TK_RPAREN and self.peek_tok()[0] != TK_EOF:
            args.append(self._parse_expr())
            if self.peek_tok()[0] == TK_OP and self.peek_tok()[1] == ",":
                self.next_tok()
        if self.peek_tok()[0] == TK_RPAREN:
            self.next_tok()

        try:
            if name == "LENGTH":
                return str(len(str(args[0])))
            elif name == "SUBSTR":
                s   = str(args[0])
                idx = int(float(args[1])) - 1
                ln  = int(float(args[2])) if len(args) > 2 else len(s) - idx
                return s[idx:idx+ln]
            elif name == "STRIP":
                s    = str(args[0])
                mode = str(args[1]).upper() if len(args) > 1 else "B"
                char = str(args[2]) if len(args) > 2 else " "
                if mode == "L": return s.lstrip(char)
                if mode == "T": return s.rstrip(char)
                return s.strip(char)
            elif name == "UPPER":
                return str(args[0]).upper()
            elif name == "LOWER":
                return str(args[0]).lower()
            elif name in ("CENTER", "CENTRE"):
                s  = str(args[0])
                n  = int(float(args[1]))
                ch = str(args[2]) if len(args) > 2 else " "
                return s.center(n, ch)
            elif name == "LEFT":
                s = str(args[0])
                n = int(float(args[1]))
                return s[:n].ljust(n)
            elif name == "RIGHT":
                s = str(args[0])
                n = int(float(args[1]))
                return s[-n:].rjust(n)
            elif name == "COPIES":
                return str(args[0]) * int(float(args[1]))
            elif name == "REVERSE":
                return str(args[0])[::-1]
            elif name == "WORDS":
                return str(len(str(args[0]).split()))
            elif name == "WORD":
                words = str(args[0]).split()
                idx   = int(float(args[1])) - 1
                return words[idx] if 0 <= idx < len(words) else ""
            elif name == "POS":
                needle = str(args[0])
                hay    = str(args[1])
                start  = int(float(args[2])) - 1 if len(args) > 2 else 0
                idx    = hay.find(needle, start)
                return str(idx + 1) if idx >= 0 else "0"
            elif name == "SPACE":
                s = str(args[0])
                n = int(float(args[1])) if len(args) > 1 else 1
                return (" " * n).join(s.split())
            elif name == "DATATYPE":
                s = str(args[0])
                t = str(args[1]).upper() if len(args) > 1 else "NUM"
                if t == "NUM":
                    try:
                        float(s)
                        return "1"
                    except Exception:
                        return "0"
                return "1" if s.isalpha() else "0"
            elif name == "ABS":
                return str(abs(float(args[0])))
            elif name == "MAX":
                return str(max(float(a) for a in args))
            elif name == "MIN":
                return str(min(float(a) for a in args))
            elif name == "SIGN":
                v = float(args[0])
                return "1" if v > 0 else ("-1" if v < 0 else "0")
            elif name == "TRUNC":
                v = float(args[0])
                n = int(float(args[1])) if len(args) > 1 else 0
                if n == 0:
                    return str(int(v))
                factor = 10 ** n
                return str(int(v * factor) / factor)
            elif name == "DATE":
                fmt = str(args[0]).upper() if args else "N"
                now = datetime.date.today()
                if fmt == "S":  return now.strftime("%Y%m%d")
                if fmt == "U":  return now.strftime("%m/%d/%y")
                if fmt == "E":  return now.strftime("%d/%m/%y")
                return now.strftime("%d %b %Y").upper()
            elif name == "TIME":
                fmt = str(args[0]).upper() if args else "N"
                now = datetime.datetime.now()
                if fmt == "H":  return str(now.hour)
                if fmt == "S":  return str(now.hour*3600 + now.minute*60 + now.second)
                return now.strftime("%H:%M:%S")
            elif name == "FORMAT":
                v = float(args[0])
                w = int(float(args[1])) if len(args) > 1 else 0
                d = int(float(args[2])) if len(args) > 2 else 2
                return f"{v:{w}.{d}f}"
        except (IndexError, ValueError) as e:
            raise RexxError(f"Error in {name}(): {e}")

        raise RexxError(f"Unknown function: {name}")

    def _math(self, left, op: str, right) -> str:
        try:
            l = float(left)
            r = float(right)
            if op == "+":   result = l + r
            elif op == "-": result = l - r
            elif op == "*": result = l * r
            elif op == "/":
                if r == 0: raise RexxError("Division by zero")
                result = l / r
            elif op == "%":
                if r == 0: raise RexxError("Division by zero")
                result = int(l) % int(r)
            elif op == "//":
                if r == 0: raise RexxError("Division by zero")
                result = int(l) // int(r)
            else:
                return str(left)
            if result == int(result):
                return str(int(result))
            return f"{result:.9g}"
        except RexxError:
            raise
        except Exception:
            raise RexxError(f"Math error: {left} {op} {right}")

    def _compare(self, left, op: str, right) -> str:
        try:
            l = float(left)
            r = float(right)
            if op == "=":           return "1" if l == r else "0"
            if op in ("\\=","<>"): return "1" if l != r else "0"
            if op == "<":           return "1" if l < r  else "0"
            if op == ">":           return "1" if l > r  else "0"
            if op == "<=":          return "1" if l <= r else "0"
            if op == ">=":          return "1" if l >= r else "0"
        except (ValueError, TypeError):
            pass
        l = str(left)
        r = str(right)
        if op == "=":           return "1" if l == r else "0"
        if op in ("\\=","<>"): return "1" if l != r else "0"
        if op == "<":           return "1" if l < r  else "0"
        if op == ">":           return "1" if l > r  else "0"
        if op == "<=":          return "1" if l <= r else "0"
        if op == ">=":          return "1" if l >= r else "0"
        return "0"


# -------------------------------------------------------------------
# INTERPRETER
# -------------------------------------------------------------------

class RexxInterpreter:
    def __init__(self, lines: list, term=None, spool_path: str = ""):
        self.source     = lines
        self.term       = term
        self.spool_path = spool_path
        self.env        = {}
        self.output     = []
        self.call_stack = []
        self.running    = True
        self.return_val = ""

    def _eval(self, expr: str) -> str:
        expr = expr.strip()
        return Evaluator(self.env).evaluate(expr)

    def _say(self, text: str):
        self.output.append(text)

    def _set_var(self, name: str, value: str):
        self.env[name.upper()] = value

    def _preprocess(self) -> list:
        full  = "\n".join(self.source)
        clean = re.sub(r"/\*.*?\*/", " ", full, flags=re.DOTALL)
        lines = clean.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            while line.endswith(","):
                line = line[:-1].strip()
                i += 1
                if i < len(lines):
                    line += " " + lines[i].strip()
            if line:
                result.append((i, line))
            i += 1
        return result

    def _find_label(self, label: str, stmts: list) -> int:
        label = label.upper().rstrip(":")
        for i, (_, text) in enumerate(stmts):
            t = text.strip().upper()
            if t == label + ":" or t.startswith(label + ":"):
                return i
        return -1

    def run(self) -> list:
        stmts = self._preprocess()
        self._execute(stmts)
        if self.spool_path:
            os.makedirs(os.path.dirname(self.spool_path), exist_ok=True)
            with open(self.spool_path, "a") as f:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n{'='*80}\n PY360 REXX OUTPUT  {now}\n{'='*80}\n")
                for line in self.output:
                    f.write(line + "\n")
                f.write(f"{'='*80}\n")
        return self.output

    def _execute(self, stmts: list):
        pc = 0
        while pc < len(stmts) and self.running:
            lineno, line = stmts[pc]
            upper = line.upper().strip()

            # Skip labels
            if re.match(r"^[A-Z_][A-Z0-9_]*\s*:$", upper):
                pc += 1
                continue

            # Skip standalone ELSE - always consumed by _exec_if
            if re.match(r"^ELSE(\s|$)", upper):
                pc += 1
                continue

            # SAY
            if upper.startswith("SAY ") or upper == "SAY":
                expr = line[3:].strip()
                self._say(self._eval(expr) if expr else "")
                pc += 1

            # EXIT
            elif upper.startswith("EXIT") or upper == "EXIT":
                parts = line.split(None, 1)
                self.return_val = self._eval(parts[1]) if len(parts) > 1 else "0"
                self.running = False
                break

            # RETURN
            elif upper.startswith("RETURN") or upper == "RETURN":
                parts = line.split(None, 1)
                self.return_val = self._eval(parts[1]) if len(parts) > 1 else ""
                if self.call_stack:
                    pc = self.call_stack.pop()
                else:
                    self.running = False
                    break

            # CALL
            elif upper.startswith("CALL "):
                label = upper[5:].strip().split()[0]
                idx   = self._find_label(label, stmts)
                if idx < 0:
                    raise RexxError(f"Label not found: {label}")
                self.call_stack.append(pc + 1)
                pc = idx + 1

            # SIGNAL
            elif upper.startswith("SIGNAL "):
                label = upper[7:].strip()
                idx   = self._find_label(label, stmts)
                if idx < 0:
                    raise RexxError(f"Label not found: {label}")
                pc = idx + 1

            # IF
            elif upper.startswith("IF "):
                pc = self._exec_if(stmts, pc)

            # DO
            elif upper.startswith("DO") and (len(upper) == 2 or upper[2] in " \t"):
                pc = self._exec_do(stmts, pc)

            # PULL
            elif upper.startswith("PULL ") or upper == "PULL":
                varname = line[4:].strip().upper() or "RESULT"
                self._set_var(varname, "")
                pc += 1

            # PARSE PULL
            elif upper.startswith("PARSE PULL "):
                varname = line[11:].strip().upper()
                self._set_var(varname, "")
                pc += 1

            # NUMERIC
            elif upper.startswith("NUMERIC "):
                pc += 1

            # Assignment
            elif "=" in line and not any(upper.startswith(k) for k in (
                    "IF ", "DO ", "SAY ", "CALL ", "SIGNAL ",
                    "PULL ", "PARSE ", "EXIT", "RETURN")):
                eq = line.index("=")
                if eq > 0 and line[eq-1] not in "<>!\\" and (
                        eq+1 >= len(line) or line[eq+1] != "="):
                    varname = line[:eq].strip().upper()
                    expr    = line[eq+1:].strip()
                    self._set_var(varname, self._eval(expr))
                pc += 1

            else:
                pc += 1

    def _exec_if(self, stmts: list, pc: int) -> int:
        _, line = stmts[pc]
        m = re.match(r"IF\s+(.+?)\s+THEN\s*(.*)", line, re.IGNORECASE)
        if not m:
            return pc + 1

        condition = m.group(1).strip()
        then_part = m.group(2).strip()
        result    = self._eval(condition)
        is_true   = result not in ("0", "", "0.0")

        if then_part:
            else_m = re.match(r"(.+?)\s+ELSE\s+(.*)", then_part, re.IGNORECASE)
            if else_m:
                if is_true:
                    self._exec_inline(else_m.group(1).strip())
                else:
                    self._exec_inline(else_m.group(2).strip())
            else:
                if is_true:
                    self._exec_inline(then_part)
            return pc + 1

        else:
            pc += 1
            if pc < len(stmts):
                _, then_line = stmts[pc]
                if is_true:
                    self._exec_inline(then_line)
                pc += 1
                if pc < len(stmts):
                    _, next_line = stmts[pc]
                    if re.match(r"(?i)^ELSE(\s|$)", next_line.strip()):
                        pc += 1  # move past ELSE line
                        if pc < len(stmts):
                            _, else_line = stmts[pc]
                            if not is_true:
                                self._exec_inline(else_line)
                            pc += 1  # move past ELSE body line
            return pc

    def _exec_inline(self, stmt: str):
        stmt  = stmt.strip()
        if not stmt:
            return
        upper = stmt.upper()

        if upper.startswith("SAY ") or upper == "SAY":
            expr = stmt[3:].strip()
            self._say(self._eval(expr) if expr else "")

        elif upper.startswith("EXIT"):
            parts = stmt.split(None, 1)
            self.return_val = self._eval(parts[1]) if len(parts) > 1 else "0"
            self.running = False

        elif upper.startswith("RETURN"):
            parts = stmt.split(None, 1)
            self.return_val = self._eval(parts[1]) if len(parts) > 1 else ""
            self.running = False

        elif "=" in stmt:
            eq = stmt.index("=")
            if eq > 0 and stmt[eq-1] not in "<>!\\" and (
                    eq+1 >= len(stmt) or stmt[eq+1] != "="):
                varname = stmt[:eq].strip().upper()
                expr    = stmt[eq+1:].strip()
                self._set_var(varname, self._eval(expr))

    def _exec_do(self, stmts: list, pc: int) -> int:
        _, line = stmts[pc]
        upper   = line.upper().strip()
        end_pc  = self._find_end(stmts, pc)
        body    = stmts[pc+1:end_pc]

        def run_body():
            self._execute(body)

        if upper == "DO FOREVER":
            while self.running:
                run_body()

        elif upper.startswith("DO WHILE "):
            cond = line[9:].strip()
            while self.running and self._eval(cond) not in ("0", ""):
                run_body()

        elif upper.startswith("DO UNTIL "):
            cond = line[9:].strip()
            run_body()
            while self.running and self._eval(cond) in ("0", ""):
                run_body()

        elif re.match(r"DO\s+\w+\s*=", upper):
            m = re.match(
                r"DO\s+(\w+)\s*=\s*(.+?)\s+TO\s+(.+?)(?:\s+BY\s+(.+))?$",
                line, re.IGNORECASE)
            if m:
                var   = m.group(1).upper()
                start = float(self._eval(m.group(2)))
                end   = float(self._eval(m.group(3)))
                step  = float(self._eval(m.group(4))) if m.group(4) else 1.0
                val   = start
                while self.running and (
                        (step > 0 and val <= end) or
                        (step < 0 and val >= end)):
                    v = int(val) if val == int(val) else val
                    self._set_var(var, str(v))
                    run_body()
                    val += step

        elif re.match(r"DO\s+\d+", upper):
            count = int(self._eval(line[3:].strip()))
            for _ in range(count):
                if not self.running:
                    break
                run_body()

        else:
            run_body()

        return end_pc + 1

    def _find_end(self, stmts: list, do_pc: int) -> int:
        depth = 1
        pc    = do_pc + 1
        while pc < len(stmts):
            _, line = stmts[pc]
            upper   = line.upper().strip()
            if upper.startswith("DO") and (len(upper) == 2 or upper[2] in " \t"):
                depth += 1
            elif upper == "END" or upper.startswith("END "):
                depth -= 1
                if depth == 0:
                    return pc
            pc += 1
        raise RexxError("DO without matching END")

    def _interactive_input(self, prompt: str) -> str:
        return ""


# -------------------------------------------------------------------
# PUBLIC ENTRY POINTS
# -------------------------------------------------------------------

def run_batch(source_path: str, spool_path: str) -> tuple:
    if not os.path.exists(source_path):
        return (8, [f"ERROR: Source not found: {source_path}"])
    with open(source_path, "r") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]
    try:
        interp = RexxInterpreter(lines, spool_path=spool_path)
        output = interp.run()
        rc     = int(float(interp.return_val)) if interp.return_val else 0
        return (rc, output)
    except RexxError as e:
        return (8, [f"REXX ERROR: {e}"])
    except Exception as e:
        return (12, [f"SYSTEM ERROR: {e}"])


def run_interactive(source_path: str, term) -> int:
    """
    Run a REXX program interactively on the terminal.
    Returns the return code.
    """
    if not os.path.exists(source_path):
        return 8
    with open(source_path, "r") as f:
        lines = [l.rstrip("\n") for l in f.readlines()]
    try:
        interp = RexxInterpreter(lines, term=term)
        output = interp.run()

        # Route output to printer spool
        try:
            import spool
            job_name = os.path.basename(source_path).replace(".txt", "")
            spool.write_to_printer(output, job_name=job_name)
        except Exception as e:
            output.append(f"SPOOL ERROR: {e}")

        # Display output on terminal
        from terminal import ATTR_NORMAL, ATTR_BOLD, ATTR_DIM, ATTR_REVERSE
        term.clear()
        term.put(0, 0, "=" * 80, ATTR_REVERSE)
        term.put(0, 2, " PY360 REXX - FOREGROUND EXECUTION ", ATTR_REVERSE)

        for i, line in enumerate(output[:20]):
            term.put(i + 2, 2, line[:76], ATTR_NORMAL)

        if len(output) > 20:
            term.put(22, 2, f"... {len(output)-20} more lines in spool", ATTR_DIM)

        term.put(23, 2, "Press any key to return to menu...", ATTR_DIM)
        term.move_cursor(23, 37)
        term.refresh()
        term.wait_key()

        rc = int(float(interp.return_val)) if interp.return_val else 0
        return rc
    except RexxError:
        return 8


# -------------------------------------------------------------------
# SELF TEST
# -------------------------------------------------------------------

if __name__ == "__main__":
    config.load()

    test_program = """\
/* PY360 REXX Self Test */
SAY "PY360 REXX Interpreter Test"
SAY COPIES("=", 40)
SAY ""
X = 10
Y = 3
SAY "X =" X
SAY "Y =" Y
SAY "X + Y =" X + Y
SAY "X * Y =" X * Y
SAY "X / Y =" X / Y
SAY "X ** 2 =" X ** 2
SAY ""
NAME = "PY360"
SAY "Name     :" NAME
SAY "Length   :" LENGTH(NAME)
SAY "Upper    :" UPPER("hello world")
SAY "Reverse  :" REVERSE(NAME)
SAY "Copies   :" COPIES("-", 20)
SAY ""
IF X > 5 THEN
  SAY "X is greater than 5"
ELSE
  SAY "X is not greater than 5"
SAY ""
SAY "Counting 1 to 5:"
DO I = 1 TO 5
  SAY "  Line" I
END
SAY ""
SAY "Date:" DATE()
SAY "Time:" TIME()
SAY ""
SAY COPIES("=", 40)
SAY "Test complete - RC = 0"
EXIT 0
"""

    lines  = test_program.strip().split("\n")
    interp = RexxInterpreter(lines)
    output = interp.run()

    print("\n=== PY360 REXX OUTPUT ===\n")
    for line in output:
        print(line)
    print(f"\nReturn code: {interp.return_val}")