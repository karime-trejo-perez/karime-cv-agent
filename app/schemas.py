"""
Modelos Pydantic para el subconjunto de la especificación Open Responses
(https://www.openresponses.org/specification) que este agente implementa.

Alcance de esta primera versión (a propósito, no por descuido):
  - POST /v1/responses, respuesta en JSON normal (sin streaming todavía).
  - `input`: string simple o lista de mensajes con role/content.
  - `previous_response_id`: para continuar una conversación (ver app/store.py).
  - `output`: un único item tipo `message` con `output_text`.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

MAX_INPUT_CHARS = 6000


def _resp_id() -> str:
    return f"resp_{uuid.uuid4().hex}"


def _msg_id() -> str:
    return f"msg_{uuid.uuid4().hex}"


class MessageItem(BaseModel):
    type: Literal["message"] = "message"
    role: Literal["user", "assistant", "system", "developer"]
    content: str | list[dict[str, Any]]

    def as_text(self) -> str:
        if isinstance(self.content, str):
            return self.content
        return "\n".join(
            part["text"] for part in self.content if isinstance(part, dict) and "text" in part
        )


class ResponsesRequest(BaseModel):
    model: str = Field(default="karime-cv-agent-1")
    input: str | list[MessageItem]
    previous_response_id: str | None = None
    store: bool = True

    @field_validator("input")
    @classmethod
    def validate_input_length(
        cls, value: str | list[MessageItem]
    ) -> str | list[MessageItem]:
        if isinstance(value, str):
            total_chars = len(value)
        else:
            total_chars = sum(len(item.as_text()) for item in value)
        if total_chars > MAX_INPUT_CHARS:
            raise ValueError(
                f"Tu mensaje es demasiado largo ({total_chars} caracteres). "
                f"El máximo permitido es {MAX_INPUT_CHARS} caracteres."
            )
        return value

    def normalized_messages(self) -> list[MessageItem]:
        if isinstance(self.input, str):
            return [MessageItem(role="user", content=self.input)]
        return self.input


class OutputTextPart(BaseModel):
    type: Literal["output_text"] = "output_text"
    text: str
    annotations: list[Any] = Field(default_factory=list)


class OutputMessageItem(BaseModel):
    id: str = Field(default_factory=_msg_id)
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    status: Literal["completed"] = "completed"
    content: list[OutputTextPart]


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ResponsesResponse(BaseModel):
    id: str = Field(default_factory=_resp_id)
    object: Literal["response"] = "response"
    created_at: int = Field(default_factory=lambda: int(time.time()))
    status: Literal["completed", "failed"] = "completed"
    model: str
    output: list[OutputMessageItem]
    previous_response_id: str | None = None
    usage: Usage = Field(default_factory=Usage)


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail