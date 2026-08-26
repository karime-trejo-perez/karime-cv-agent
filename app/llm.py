"""
Integración con Claude (Anthropic API).

Enfoque elegido: mandamos el CV completo (vía context_loader) como system
prompt en cada llamada, en vez de usar "tool calling" para pedir datos por
partes. Es la opción más simple y suficiente dado que el CV completo son
menos de 1,000 palabras — no hay riesgo de acercarnos a límites de contexto.
"""

import os

import anthropic

from app.context_loader import load_system_prompt

MODEL_NAME = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

TEMPERATURE = 0.4
MAX_TOKENS = 1024

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta la variable de entorno ANTHROPIC_API_KEY. "
                "Revisa que tu archivo .env exista y tenga tu clave real."
            )
        _client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
    return _client


def generate_reply(conversation_messages: list[dict]) -> tuple[str, dict]:
    client = get_client()

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        system=load_system_prompt(),
        messages=conversation_messages,
        extra_body={"temperature": TEMPERATURE},
    )

    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return text, usage