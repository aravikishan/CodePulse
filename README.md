<div align="center">

# CodePulse

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)
![CI](https://github.com/ravikishan/CodePulse/actions/workflows/ci.yml/badge.svg)
![Code Style](https://img.shields.io/badge/code%20style-flake8-blue)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

**A Python code analysis tool** that provides real-time insights into code
complexity, quality metrics, and code smells using AST (Abstract Syntax Tree)
parsing. Analyze your Python code in seconds -- right from your browser.

[Getting Started](#quick-start) |
[Features](#features) |
[API Docs](#api-documentation) |
[Architecture](#architecture)

</div>

---

## Screenshots

| Dashboard | Code Analysis |
|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Analysis](screenshots/analysis.png) |

| Analysis Results | History |
|---|---|
| ![Results](screenshots/results.png) | ![History](screenshots/history.png) |

---

## Features

### Core Analysis Engine

- **AST-Based Parsing** -- Parses Python source into an Abstract Syntax Tree
  for accurate structural analysis without executing the code.

- **Cyclomatic Complexity** -- Counts branches (`if`, `elif`, `for`, `while`,
  `except`, `with`, `and`/`or`, `assert`, comprehensions) to compute
  per-function and overall complexity scores.

- **Halstead Metrics** -- Quantifies code using operators and operands:
  - **Volume** -- size of the implementation
  - **Difficulty** -- how hard to understand
  - **Effort** -- mental effort to develop
  - **Estimated Bugs** -- expected defect count
  - **Estimated Time** -- development time in seconds

- **Maintainability Index** -- Composite score (0--100) using the Microsoft
  variant: `MI = max(0, (171 - 5.2*ln(V) - 0.23*G - 16.2*ln(LOC)) * 100/171)`

### Code Smell Detection

| Smell | Threshold | Severity |
|---|---|---|
| Long function | >50 lines | Warning |
| Too many parameters | >5 params | Warning |
| Deep nesting | >4 levels | Warning |
| High complexity | >10 per function | Warning |
| Missing docstring | Public functions/classes | Info |
| Unused import | Name not referenced | Info |
| Magic number | Literals >10 | Info |
| God class | >15 methods | Warning |
| Duplicate code | >= 4 identical lines | Warning |

### Additional Features

- **Function & Class Extraction** -- Lists every function and class with line
  numbers, argument counts, decorators, and method details.
- **Letter Grading** -- Assigns a grade (A--F) based on maintainability index,
  complexity, and smell count.
- **Analysis History** -- Persists every analysis to SQLite for reviewing past
  results with aggregate statistics.
- **REST API** -- Fully functional JSON API for integration with CI/CD
  pipelines and external tools.
- **Dashboard** -- Overview with aggregate stats, grade distribution chart,
  and recent analyses.
- **Dark-Themed UI** -- Clean, responsive interface with CodeMirror editor
  and Chart.js visualizations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.0 |
| Database | SQLite via SQLAlchemy 2.0 |
| Validation | Pydantic 2.5 |
| Analysis | Python `ast` module (stdlib) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Code Editor | CodeMirror 5.65 |
| Charts | Chart.js 4.4 |
| Testing | pytest 7.4, pytest-cov |
| Deployment | Docker, Docker Compose, Gunicorn |
| CI/CD | GitHub Actions |

---

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/ravikishan/CodePulse.git
cd CodePulse

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:8000`.

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Or build and run manually
docker build -t codepulse .
docker run -p 8000:8000 codepulse
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `CODEPULSE_PORT` | `8000` | Server port |
| `CODEPULSE_DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | `codepulse-dev-secret` | Flask secret key |
| `DATABASE_URL` | `sqlite:///instance/codepulse.db` | Database URI |

---

## API Documentation

### Health Check

```
GET /api/health
```

Response:
```json
{"status": "healthy", "service": "CodePulse", "version": "1.0.0"}
```

### Analyze Code

```
POST /api/analyze
Content-Type: application/json

{
  "code": "def hello():\n    return 'world'\n",
  "filename": "hello.py"
}
```

Response:
```json
{
  "filename": "hello.py",
  "language": "python",
  "total_lines": 2,
  "code_lines": 2,
  "blank_lines": 0,
  "comment_lines": 0,
  "complexity_score": 1,
  "maintainability_index": 89.2,
  "halstead_volume": 15.51,
  "halstead_difficulty": 1.5,
  "halstead_effort": 23.26,
  "halstead_bugs": 0.005,
  "halstead_time": 1.29,
  "grade": "A",
  "functions": [...],
  "classes": [],
  "imports": [],
  "smells": [],
  "smell_count": 0,
  "functions_count": 1,
  "classes_count": 0,
  "id": 1
}
```

### List Recent Analyses

```
GET /api/analyses?limit=20
```

### Get Single Analysis

```
GET /api/analyses/<id>
```

### Delete Analysis

```
DELETE /api/analyses/<id>
```

### Aggregate Statistics

```
GET /api/stats
```

Response:
```json
{
  "total_analyses": 42,
  "avg_complexity": 5.3,
  "avg_mi": 72.1,
  "avg_smells": 2.1,
  "total_lines_analyzed": 15230,
  "avg_lines": 362.6,
  "grade_distribution": {"A": 15, "B": 12, "C": 8, "D": 5, "F": 2}
}
```

### Get Sample Code

```
GET /api/sample
```

---

## Architecture

```
CodePulse/
|-- app.py                      # Flask app factory & entry point
|-- config.py                   # Application configuration & constants
|-- models/
|   |-- __init__.py             # Package exports
|   |-- database.py             # SQLAlchemy initialization
|   |-- schemas.py              # ORM models & Pydantic schemas
|-- services/
|   |-- __init__.py             # Package exports
|   |-- analyzer.py             # AST analysis engine (complexity, Halstead, MI)
|   |-- data_service.py         # Data access, queries, sample data
|-- routes/
|   |-- __init__.py             # Package exports
|   |-- api.py                  # REST API endpoints (/api/*)
|   |-- views.py                # HTML view routes (/, /analyze, /history, /about)
|-- templates/
|   |-- base.html               # Base layout with nav, footer, CDN links
|   |-- index.html              # Dashboard with stats & charts
|   |-- analyze.html            # Code input & analysis results
|   |-- history.html            # Analysis history table
|   |-- about.html              # Feature docs, API reference, grading scale
|-- static/
|   |-- css/style.css           # Dark theme design system (~250 lines)
|   |-- js/main.js              # CodeMirror, Chart.js, API calls (~300 lines)
|-- tests/
|   |-- conftest.py             # pytest fixtures
|   |-- test_api.py             # API endpoint tests
|   |-- test_models.py          # Model/schema tests
|   |-- test_services.py        # Analyzer & data service tests
|-- seed_data/data.json         # Sample snippets & expected results
|-- Dockerfile                  # Production Docker image
|-- docker-compose.yml          # Docker Compose configuration
|-- start.sh                    # Startup script (gunicorn or dev server)
|-- .github/workflows/ci.yml   # Lint + test + Docker build
|-- requirements.txt            # Pinned Python dependencies
```

### Analysis Flow

```
User Input (code) --> /api/analyze --> analyzer.py
                                          |
                                   ast.parse(code)
                                          |
                          +---------------+---------------+
                          |               |               |
                     Functions       Halstead        Code Smells
                     Classes         Metrics         Detection
                     Imports         Volume          9 smell types
                     Complexity      Difficulty
                                     Effort
                          |               |               |
                          +-------+-------+-------+-------+
                                  |
                         Maintainability Index
                         Grade Computation
                                  |
                         Save to SQLite
                                  |
                         JSON Response --> UI Rendering
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run a specific test file
pytest tests/test_services.py -v

# Run a specific test
pytest tests/test_services.py::test_halstead_metrics -v
```

### Test Coverage

The test suite includes **15 tests** covering:
- API endpoint behavior (health, analyze, list, retrieve, stats)
- Database model creation and serialization
- Pydantic schema validation
- AST analysis accuracy (complexity, functions, classes, imports)
- Code smell detection (long functions, too many params, etc.)
- Halstead metric computation
- Maintainability index calculation
- Edge cases (syntax errors, empty code)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest tests/ -v`)
5. Lint your code (`flake8 . --max-line-length=120`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## License

This project is licensed under the MIT License -- see the [LICENSE](LICENSE)
file for details.

---

<div align="center">

**Built with Python, Flask, and the AST module.**

[Report Bug](https://github.com/ravikishan/CodePulse/issues) |
[Request Feature](https://github.com/ravikishan/CodePulse/issues)

</div>
