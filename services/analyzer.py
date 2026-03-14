"""Core analysis engine -- AST-based Python code analysis.

Provides cyclomatic complexity scoring, Halstead metrics,
maintainability index calculation, and code smell detection.
"""

import ast
import math
import re
from collections import Counter
from typing import Any


# ======================================================================
# Halstead metric helpers
# ======================================================================

# AST node types that count as operators
_OPERATOR_NODES = (
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv,
    ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.MatMult,
    ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
)

# AST node types treated as operator keywords
_KEYWORD_OPERATORS = (
    ast.If, ast.For, ast.While, ast.With, ast.Return, ast.Yield,
    ast.YieldFrom, ast.Raise, ast.Try, ast.Assert, ast.Delete,
    ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal,
    ast.Break, ast.Continue, ast.Pass, ast.Lambda,
    ast.Assign, ast.AugAssign, ast.AnnAssign,
)


def _collect_halstead(tree: ast.AST) -> dict[str, Any]:
    """Walk the AST and collect Halstead operator/operand counts.

    Returns a dict with keys:
        n1  -- number of distinct operators
        n2  -- number of distinct operands
        N1  -- total number of operators
        N2  -- total number of operands
        vocabulary, length, volume, difficulty, effort, bugs, time
    """
    operators: list[str] = []
    operands: list[str] = []

    for node in ast.walk(tree):
        # -- operators from expression nodes ---
        if isinstance(node, ast.BinOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.UnaryOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.BoolOp):
            operators.append(type(node.op).__name__)
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                operators.append(type(op).__name__)
        elif isinstance(node, ast.Call):
            operators.append("()")
        elif isinstance(node, ast.Subscript):
            operators.append("[]")
        elif isinstance(node, ast.Attribute):
            operators.append(".")
        elif isinstance(node, _KEYWORD_OPERATORS):
            operators.append(type(node).__name__)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            operators.append("def")
        elif isinstance(node, ast.ClassDef):
            operators.append("class")

        # -- operands ---
        if isinstance(node, ast.Name):
            operands.append(node.id)
        elif isinstance(node, ast.Constant):
            operands.append(repr(node.value))
        elif isinstance(node, ast.arg):
            operands.append(node.arg)

    n1 = len(set(operators)) or 1
    n2 = len(set(operands)) or 1
    cap_n1 = len(operators) or 1
    cap_n2 = len(operands) or 1

    vocabulary = n1 + n2
    length = cap_n1 + cap_n2
    volume = length * math.log2(vocabulary) if vocabulary > 0 else 0.0
    difficulty = (n1 / 2.0) * (cap_n2 / n2) if n2 > 0 else 0.0
    effort = difficulty * volume
    bugs = volume / 3000.0
    time_seconds = effort / 18.0

    return {
        "n1": n1,
        "n2": n2,
        "N1": cap_n1,
        "N2": cap_n2,
        "vocabulary": vocabulary,
        "length": length,
        "volume": round(volume, 2),
        "difficulty": round(difficulty, 2),
        "effort": round(effort, 2),
        "bugs": round(bugs, 3),
        "time": round(time_seconds, 2),
    }


# ======================================================================
# Cyclomatic complexity helpers
# ======================================================================


def _count_branches(node: ast.AST) -> int:
    """Recursively count branch/complexity-increasing nodes."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            # each `and` / `or` adds a branch
            count += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            count += 1
        elif isinstance(child, ast.comprehension):
            count += 1
            count += len(child.ifs)
    return count


def _function_complexity(node: ast.AST) -> int:
    """Cyclomatic complexity of a single function (starts at 1)."""
    return 1 + _count_branches(node)


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    """Return the maximum nesting depth inside *node*."""
    nesting_types = (ast.If, ast.For, ast.While, ast.With, ast.Try)
    max_d = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, nesting_types):
            max_d = max(max_d, _max_nesting(child, depth + 1))
        else:
            max_d = max(max_d, _max_nesting(child, depth))
    return max_d


# ======================================================================
# Maintainability index
# ======================================================================


def _maintainability_index(
    halstead_volume: float,
    cyclomatic_complexity: int,
    lines_of_code: int,
) -> float:
    """Compute the maintainability index (0-100 scale).

    Uses the Microsoft variant:
        MI = max(0, (171 - 5.2*ln(V) - 0.23*G - 16.2*ln(LOC)) * 100/171)
    where V = Halstead volume, G = cyclomatic complexity, LOC = lines of code.
    """
    if lines_of_code <= 0:
        return 100.0
    vol = max(halstead_volume, 1.0)
    loc = max(lines_of_code, 1)
    cc = max(cyclomatic_complexity, 1)

    raw = 171.0 - 5.2 * math.log(vol) - 0.23 * cc - 16.2 * math.log(loc)
    scaled = max(0.0, raw * 100.0 / 171.0)
    return round(min(scaled, 100.0), 1)


# ======================================================================
# Code smell detection helpers
# ======================================================================


def _detect_magic_numbers(source: str) -> list[dict[str, Any]]:
    """Find magic number literals (ints > 10 not in common patterns)."""
    magic: list[dict[str, Any]] = []
    allowed = {0, 1, 2, 3, 10, 100, 1000, -1}
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("def ") or stripped.startswith("class "):
            continue
        if "=" in stripped and stripped.split("=")[0].strip().isupper():
            continue  # skip constant assignments like MAX_SIZE = 4096
        for match in re.finditer(r"(?<![\w.])(-?\d+)(?![\w.])", stripped):
            try:
                val = int(match.group(1))
            except ValueError:
                continue
            if val not in allowed and abs(val) > 10:
                magic.append({"line": i, "value": val})
    return magic


def _detect_duplicate_blocks(source: str) -> list[dict[str, Any]]:
    """Detect duplicated code blocks (consecutive identical line groups >= 4 lines)."""
    lines = source.splitlines()
    duplicates: list[dict[str, Any]] = []
    block_size = 4
    seen: dict[str, int] = {}

    for i in range(len(lines) - block_size + 1):
        block = "\n".join(line.strip() for line in lines[i : i + block_size])
        if not block.strip():
            continue
        if block in seen:
            duplicates.append({
                "line": i + 1,
                "original_line": seen[block],
                "block_size": block_size,
            })
        else:
            seen[block] = i + 1

    return duplicates[:5]  # cap at 5


def _detect_god_class(classes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect classes with too many methods (god class smell)."""
    smells: list[dict[str, Any]] = []
    for cls in classes:
        if cls.get("method_count", 0) > 15:
            smells.append({
                "type": "god_class",
                "message": (
                    f"Class '{cls['name']}' has {cls['method_count']} methods "
                    f"(consider splitting into smaller classes)"
                ),
                "severity": "warning",
                "line": cls.get("line", 0),
            })
    return smells


# ======================================================================
# Main public API
# ======================================================================


def analyze_code(source_code: str, filename: str = "untitled.py") -> dict[str, Any]:
    """Analyze Python source code and return a comprehensive report.

    Returns a dict with keys: total_lines, blank_lines, comment_lines,
    code_lines, functions, classes, imports, complexity_score, smells,
    grade, halstead metrics, maintainability_index, etc.
    """
    lines = source_code.splitlines()
    total_lines = len(lines)
    blank_lines = sum(1 for ln in lines if not ln.strip())
    comment_lines = sum(1 for ln in lines if ln.strip().startswith("#"))
    code_lines = total_lines - blank_lines - comment_lines

    # -- Parse AST --
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as exc:
        return {
            "filename": filename,
            "language": "python",
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "functions": [],
            "classes": [],
            "imports": [],
            "complexity_score": 0,
            "maintainability_index": 0.0,
            "halstead_volume": 0.0,
            "halstead_difficulty": 0.0,
            "halstead_effort": 0.0,
            "halstead_bugs": 0.0,
            "halstead_time": 0.0,
            "smells": [{"type": "syntax_error", "message": str(exc), "severity": "error"}],
            "smell_count": 1,
            "functions_count": 0,
            "classes_count": 0,
            "grade": "F",
        }

    # -- Extract functions ---
    functions: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            func_lines = end_line - node.lineno + 1
            args = [a.arg for a in node.args.args]
            complexity = _function_complexity(node)
            nesting = _max_nesting(node)
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    decorators.append(ast.dump(dec))
                elif isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Name):
                        decorators.append(dec.func.id)

            has_docstring = (
                isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ) if node.body else False

            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": end_line,
                "args": args,
                "arg_count": len(args),
                "complexity": complexity,
                "lines": func_lines,
                "nesting_depth": nesting,
                "decorators": decorators,
                "has_docstring": has_docstring,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })

    # -- Extract classes ---
    classes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in ast.iter_child_nodes(node):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(n.name)
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.dump(base))

            has_docstring = (
                isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ) if node.body else False

            end_line = getattr(node, "end_lineno", node.lineno)
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": end_line,
                "methods": methods,
                "method_count": len(methods),
                "bases": bases,
                "has_docstring": has_docstring,
                "lines": end_line - node.lineno + 1,
            })

    # -- Extract imports ---
    imports: list[dict[str, Any]] = []
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "type": "import",
                })
                imported_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append({
                    "module": f"{module}.{alias.name}" if module else alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "type": "from_import",
                })
                imported_names.add(name)

    # -- Halstead metrics ---
    halstead = _collect_halstead(tree)

    # -- Cyclomatic complexity ---
    total_complexity = (
        sum(f["complexity"] for f in functions)
        if functions
        else _count_branches(tree) + 1
    )

    # -- Maintainability index ---
    mi = _maintainability_index(halstead["volume"], total_complexity, code_lines)

    # -- Detect code smells ---
    smells: list[dict[str, Any]] = []

    # 1. Long functions (>50 lines)
    for f in functions:
        if f["lines"] > 50:
            smells.append({
                "type": "long_function",
                "message": (
                    f"Function '{f['name']}' is {f['lines']} lines long "
                    f"(recommended max 50)"
                ),
                "severity": "warning",
                "line": f["line"],
            })

    # 2. Too many parameters (>5)
    for f in functions:
        if f["arg_count"] > 5:
            smells.append({
                "type": "too_many_params",
                "message": (
                    f"Function '{f['name']}' has {f['arg_count']} parameters "
                    f"(recommended max 5)"
                ),
                "severity": "warning",
                "line": f["line"],
            })

    # 3. Deep nesting (>4 levels)
    for f in functions:
        if f["nesting_depth"] > 4:
            smells.append({
                "type": "deep_nesting",
                "message": (
                    f"Function '{f['name']}' has nesting depth "
                    f"{f['nesting_depth']} (recommended max 4)"
                ),
                "severity": "warning",
                "line": f["line"],
            })

    # 4. High function complexity (>10)
    for f in functions:
        if f["complexity"] > 10:
            smells.append({
                "type": "high_complexity",
                "message": (
                    f"Function '{f['name']}' has cyclomatic complexity "
                    f"{f['complexity']} (recommended max 10)"
                ),
                "severity": "warning",
                "line": f["line"],
            })

    # 5. Missing docstrings
    for f in functions:
        if not f["has_docstring"] and not f["name"].startswith("_"):
            smells.append({
                "type": "missing_docstring",
                "message": f"Public function '{f['name']}' is missing a docstring",
                "severity": "info",
                "line": f["line"],
            })

    for c in classes:
        if not c["has_docstring"]:
            smells.append({
                "type": "missing_docstring",
                "message": f"Class '{c['name']}' is missing a docstring",
                "severity": "info",
                "line": c["line"],
            })

    # 6. Unused imports (heuristic: name not found elsewhere in source)
    code_without_imports = "\n".join(
        ln for ln in lines
        if not ln.strip().startswith("import ") and not ln.strip().startswith("from ")
    )
    for imp in imports:
        name = imp["alias"] if imp["alias"] else imp["module"].split(".")[-1]
        if name not in code_without_imports:
            smells.append({
                "type": "unused_import",
                "message": f"Import '{name}' appears unused",
                "severity": "info",
                "line": imp["line"],
            })

    # 7. Magic numbers
    magic_nums = _detect_magic_numbers(source_code)
    for m in magic_nums[:5]:
        smells.append({
            "type": "magic_number",
            "message": f"Magic number {m['value']} on line {m['line']}",
            "severity": "info",
            "line": m["line"],
        })

    # 8. God classes
    smells.extend(_detect_god_class(classes))

    # 9. Duplicate code blocks
    for dup in _detect_duplicate_blocks(source_code):
        smells.append({
            "type": "duplicate_code",
            "message": (
                f"Duplicated {dup['block_size']}-line block at line {dup['line']} "
                f"(original at line {dup['original_line']})"
            ),
            "severity": "warning",
            "line": dup["line"],
        })

    # -- Grade ---
    grade = _compute_grade(total_complexity, len(smells), mi)

    return {
        "filename": filename,
        "language": "python",
        "total_lines": total_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "complexity_score": total_complexity,
        "maintainability_index": mi,
        "halstead_volume": halstead["volume"],
        "halstead_difficulty": halstead["difficulty"],
        "halstead_effort": halstead["effort"],
        "halstead_bugs": halstead["bugs"],
        "halstead_time": halstead["time"],
        "smells": smells,
        "smell_count": len(smells),
        "functions_count": len(functions),
        "classes_count": len(classes),
        "grade": grade,
    }


def _compute_grade(complexity: int, smell_count: int, mi: float) -> str:
    """Compute a letter grade from complexity, smell count, and MI.

    The maintainability index (0-100) is the primary signal; complexity
    and smell count push the score downward.
    """
    # Start from MI score, penalize for smells and complexity
    adjusted = mi - (smell_count * 1.5) - (max(0, complexity - 10) * 0.5)
    if adjusted >= 75:
        return "A"
    elif adjusted >= 55:
        return "B"
    elif adjusted >= 35:
        return "C"
    elif adjusted >= 15:
        return "D"
    return "F"
