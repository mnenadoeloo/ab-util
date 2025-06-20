from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

# Значения по умолчанию
DEFAULT_TIMEOUT = 5
DEFAULT_MODE = "triple" 