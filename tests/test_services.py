"""Service-layer tests for CodePulse."""

from services.analyzer import analyze_code, _collect_halstead, _maintainability_index
from services.data_service import get_sample_code

import ast


def test_analyze_simple_code():
    """A trivial function should receive a low complexity score."""
    code = "def greet(name):\n    return f'Hello, {name}'\n"
    result = analyze_code(code, "greet.py")
    assert result["functions_count"] == 1
    assert result["complexity_score"] <= 2
    assert result["grade"] == "A"
    assert result["maintainability_index"] > 50


def test_analyze_complex_code():
    """Code with many branches gets a higher complexity score."""
    code = '''
def route(request, db, cache, logger, config, extra):
    if request.method == "GET":
        for item in db.query():
            if item.active:
                if item.score > 0:
                    try:
                        cache.set(item.id, item)
                    except Exception:
                        logger.error("fail")
            elif item.score < 0:
                pass
        if config.debug:
            logger.info("done")
    elif request.method == "POST":
        while not db.ready():
            pass
    return None
'''
    result = analyze_code(code, "route.py")
    assert result["complexity_score"] >= 5
    assert result["grade"] in ("B", "C", "D", "F")
    assert result["halstead_volume"] > 0


def test_detect_long_function():
    """A function exceeding 50 lines triggers the long_function smell."""
    lines = ["def big_func():"]
    for i in range(55):
        lines.append(f"    x_{i} = {i}")
    code = "\n".join(lines) + "\n"
    result = analyze_code(code, "big.py")
    smell_types = [s["type"] for s in result["smells"]]
    assert "long_function" in smell_types


def test_detect_too_many_params():
    """A function with >5 parameters triggers the too_many_params smell."""
    code = "def many(a, b, c, d, e, f, g):\n    pass\n"
    result = analyze_code(code, "many.py")
    smell_types = [s["type"] for s in result["smells"]]
    assert "too_many_params" in smell_types


def test_detect_high_complexity():
    """A function with complexity >10 triggers the high_complexity smell."""
    branches = "\n".join(
        [f"        if x == {i}:" for i in range(12)]
    )
    code = f"def tangled(x):\n    y = 0\n    for i in range(x):\n{branches}\n            y += 1\n    return y\n"
    result = analyze_code(code, "tangled.py")
    smell_types = [s["type"] for s in result["smells"]]
    assert "high_complexity" in smell_types


def test_detect_missing_docstring():
    """A public function without a docstring triggers missing_docstring."""
    code = "def public_func():\n    return 42\n"
    result = analyze_code(code, "nodoc.py")
    smell_types = [s["type"] for s in result["smells"]]
    assert "missing_docstring" in smell_types


def test_grade_calculation():
    """Grade A should be assigned to simple, clean code."""
    code = "x = 1\n"
    result = analyze_code(code, "simple.py")
    assert result["grade"] == "A"


def test_syntax_error_returns_grade_f():
    """Unparseable code should receive an F grade."""
    code = "def broken(:\n"
    result = analyze_code(code, "broken.py")
    assert result["grade"] == "F"
    assert any(s["type"] == "syntax_error" for s in result["smells"])


def test_class_extraction():
    """Classes and their methods are extracted correctly."""
    code = '''
class Animal:
    """Base animal."""
    def speak(self):
        pass

    def eat(self):
        pass

class Dog(Animal):
    """A dog."""
    def speak(self):
        return "woof"
'''
    result = analyze_code(code, "animals.py")
    assert result["classes_count"] == 2
    class_names = [c["name"] for c in result["classes"]]
    assert "Animal" in class_names
    assert "Dog" in class_names


def test_halstead_metrics():
    """Halstead metrics are computed for non-trivial code."""
    code = "x = 1 + 2\ny = x * 3\nz = x + y\n"
    tree = ast.parse(code)
    h = _collect_halstead(tree)
    assert h["volume"] > 0
    assert h["difficulty"] > 0
    assert h["effort"] > 0
    assert h["bugs"] >= 0


def test_maintainability_index():
    """MI returns a value between 0 and 100."""
    mi = _maintainability_index(100.0, 5, 50)
    assert 0 <= mi <= 100

    # Extreme case: very high volume/complexity
    mi_bad = _maintainability_index(10000.0, 100, 500)
    assert mi_bad < mi


def test_sample_code_not_empty():
    """get_sample_code() returns a non-empty string."""
    sample = get_sample_code()
    assert isinstance(sample, str)
    assert len(sample) > 50


def test_import_extraction():
    """Imports are correctly extracted with type info."""
    code = "import os\nfrom sys import argv\n\nprint(os.getcwd(), argv)\n"
    result = analyze_code(code, "imports.py")
    assert len(result["imports"]) == 2
    types = [imp["type"] for imp in result["imports"]]
    assert "import" in types
    assert "from_import" in types


def test_code_lines_count():
    """code_lines correctly excludes blanks and comments."""
    code = "# comment\n\nx = 1\ny = 2\n\n# another comment\n"
    result = analyze_code(code, "count.py")
    assert result["total_lines"] == 6
    assert result["blank_lines"] == 2
    assert result["comment_lines"] == 2
    assert result["code_lines"] == 2
