"""
Store de conversaciones en memoria del proceso, indexado por response_id.

Decisión de diseño: para el alcance de este reto (demo + evaluación), un
diccionario en memoria es suficiente y evita la complejidad operativa de una
base de datos externa. Es una limitación consciente y documentada:

  - Se pierde el historial si el contenedor se reinicia (aceptable: Cloud Run
    puede escalar a 0 y volver a levantar instancias).
  - No escala horizontalmente entre múltiples instancias del contenedor.

Para producción real, este módulo se reemplazaría por Redis o una tabla en
Postgres, sin tocar el resto de la aplicación (la interfaz `get`/`put` se
mantendría igual).
"""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_STORE: dict[str, list[dict[str, Any]]] = {}

_MAX_ENTRIES = 500  # límite simple para evitar crecimiento sin control en memoria


def put(response_id: str, anthropic_messages: list[dict[str, Any]]) -> None:
    with _lock:
        if len(_STORE) >= _MAX_ENTRIES:
            oldest_key = next(iter(_STORE))
            _STORE.pop(oldest_key, None)
        _STORE[response_id] = anthropic_messages


def get(response_id: str) -> list[dict[str, Any]] | None:
    with _lock:
        return _STORE.get(response_id)