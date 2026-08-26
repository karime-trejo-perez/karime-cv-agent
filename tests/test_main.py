"""
Pruebas del servidor FastAPI (app/main.py).

Se usa unittest.mock.patch sobre app.llm.generate_reply para no llamar a
la API real de Anthropic en cada corrida de tests (evita gastar tokens y
depender de que ANTHROPIC_API_KEY exista en el entorno de pruebas).
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_responde_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "karime-cv-agent"}


@patch("app.llm.generate_reply")
def test_pregunta_normal_arma_bien_el_json_de_salida(mock_generate_reply):
    mock_generate_reply.return_value = (
        "Karime tiene experiencia en evaluación de LLMs.",
        {"input_tokens": 100, "output_tokens": 20},
    )

    response = client.post(
        "/v1/responses", json={"input": "¿Qué experiencia tienes?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["output"][0]["content"][0]["text"] == (
        "Karime tiene experiencia en evaluación de LLMs."
    )
    assert body["usage"]["input_tokens"] == 100
    assert body["usage"]["output_tokens"] == 20
    assert body["usage"]["total_tokens"] == 120


def test_input_vacio_devuelve_400():
    response = client.post("/v1/responses", json={"input": []})
    assert response.status_code == 400


def test_previous_response_id_inexistente_devuelve_404():
    response = client.post(
        "/v1/responses",
        json={"input": "hola", "previous_response_id": "resp_no_existe"},
    )
    assert response.status_code == 404


def test_falta_el_campo_input_devuelve_400_o_422():
    response = client.post("/v1/responses", json={})
    assert response.status_code in (400, 422)
