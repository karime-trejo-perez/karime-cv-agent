"""
Carga el contenido de rules.md y de todos los archivos .md en cv_data/, y los
junta en un solo bloque de texto que se usa como "system prompt" (las
instrucciones que el modelo recibe antes de cada pregunta).

Por qué esto vive en su propio archivo, separado de main.py: así podemos
probarlo de forma aislada (ver tests/test_context_loader.py) sin necesitar
un servidor corriendo, y si mañana cambia de dónde vienen los datos (otra
carpeta, otra fuente), solo se toca este archivo.
"""

import functools
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = BASE_DIR / "rules.md"
CV_DATA_DIR = BASE_DIR / "cv_data"


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


@functools.lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Arma el system prompt completo: rules.md + todos los .md de cv_data/.

    Usamos @lru_cache para que los archivos se lean del disco UNA sola vez
    mientras el servidor está corriendo, no en cada pregunta que llegue —
    el contenido no cambia durante la ejecución, así que releerlo cada vez
    sería trabajo innecesario.
    """
    if not RULES_PATH.exists():
        raise RuntimeError(f"No se encontró rules.md en {RULES_PATH}")

    sections = [_read_file(RULES_PATH), "# Información del CV (fuente de verdad)"]

    md_files = sorted(CV_DATA_DIR.glob("*.md"))
    if not md_files:
        raise RuntimeError(f"No se encontraron archivos .md en {CV_DATA_DIR}")

    for path in md_files:
        sections.append(_read_file(path))

    return "\n\n---\n\n".join(sections)