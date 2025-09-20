import sys
from pathlib import Path

# Garante que o diretório do projeto esteja no sys.path para importar `tests.*`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytest_plugins = (
    "tests.fixtures.common.paths",
    "tests.fixtures.infrastructure.loader_text",
    "tests.fixtures.cli.args",
    "tests.fixtures.domain.interfaces",
)
