"""
Servidor FastAPI. Expone:
  GET  /health        -> chequeo simple de que el servidor está vivo
  POST /v1/responses  -> el endpoint que la plataforma de Banorte usará
"""

from __future__ import annotations

import logging
import time
import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import llm, store
from app.logging_config import configure_logging
from app.schemas import (
    ErrorDetail,
    ErrorResponse,
    OutputMessageItem,
    OutputTextPart,
    ResponsesRequest,
    ResponsesResponse,
    Usage,
)

configure_logging()
logger = logging.getLogger("karime_agent.api")

app = FastAPI(
    title="Karime Trejo Pérez — CV Agent",
    description="Agente conversacional sobre el perfil profesional de Karime, compatible con Open Responses.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "agent": "karime-cv-agent"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"] if part != "body")
    error_msg = first_error["msg"].removeprefix("Value error, ")
    message = f"{field}: {error_msg}" if field else error_msg
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                message=message, type="invalid_request", param=field or None
            )
        ).model_dump(),
    )


def _build_conversation(req: ResponsesRequest) -> list[dict]:
    prior_messages: list[dict] = []

    if req.previous_response_id:
        found = store.get(req.previous_response_id)
        if found is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "message": f"previous_response_id '{req.previous_response_id}' no encontrado.",
                        "type": "invalid_request",
                        "param": "previous_response_id",
                        "code": "previous_response_not_found",
                    }
                },
            )
        prior_messages = found

    new_messages = []
    for item in req.normalized_messages():
        if item.role not in ("user", "assistant"):
            logger.info("ignored_non_conversational_role", extra={"role": item.role})
            continue
        new_messages.append({"role": item.role, "content": item.as_text()})

    if not new_messages:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": "No se encontró un mensaje de usuario válido en `input`.",
                    "type": "invalid_request",
                    "param": "input",
                    "code": None,
                }
            },
        )

    return prior_messages + new_messages


@app.post("/v1/responses")
async def create_response(req: ResponsesRequest):
    started = time.time()
    conversation = _build_conversation(req)

    try:
        final_text, usage = llm.generate_reply(conversation)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(message=str(exc), type="server_error")
            ).model_dump(),
        )
    except Exception:
        logger.exception("agent_turn_failed")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(message="Error interno del agente.", type="server_error")
            ).model_dump(),
        )

    conversation_with_reply = conversation + [{"role": "assistant", "content": final_text}]

    response_id = f"resp_{uuid.uuid4().hex}"
    if req.store:
        store.put(response_id, conversation_with_reply)

    resp = ResponsesResponse(
        id=response_id,
        model=req.model,
        output=[OutputMessageItem(content=[OutputTextPart(text=final_text)])],
        previous_response_id=req.previous_response_id,
        usage=Usage(
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            total_tokens=usage["input_tokens"] + usage["output_tokens"],
        ),
    )

    logger.info(
        "request_completed",
        extra={
            "response_id": response_id,
            "latency_ms": round((time.time() - started) * 1000, 1),
            "usage": usage,
        },
    )

    return JSONResponse(content=resp.model_dump(mode="json"))