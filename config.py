"""Application configuration for CodePulse."""

import os

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("CODEPULSE_PORT", 8000))
DEBUG = os.environ.get("CODEPULSE_DEBUG", "false").lower() == "true"

# Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "instance", "codepulse.db")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
)

# Uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

# Analysis thresholds
SUPPORTED_LANGUAGES = ["python"]
MAX_CODE_LENGTH = 500_000  # characters
COMPLEXITY_THRESHOLDS = {
    "A": (0, 5),
    "B": (6, 10),
    "C": (11, 20),
    "D": (21, 40),
    "F": (41, float("inf")),
}
LONG_FUNCTION_THRESHOLD = 50
MAX_PARAMS_THRESHOLD = 5
MAX_NESTING_THRESHOLD = 4
MAINTAINABILITY_THRESHOLDS = {
    "A": (80, 100),
    "B": (60, 79),
    "C": (40, 59),
    "D": (20, 39),
    "F": (0, 19),
}

# Testing
TESTING = False
