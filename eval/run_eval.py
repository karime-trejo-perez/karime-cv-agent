"""
Script de evaluación funcional para el agente de CV.

A diferencia de un unit test (que prueba código determinista sin llamar a
la API real), esto manda preguntas reales al servidor corriendo en vivo,
y revisa la respuesta REAL del modelo contra criterios de aceptación
simples basados en texto:

  - must_include_any: la respuesta debe contener AL MENOS UNA de estas
    frases (comparación simple, insensible a mayúsculas).
  - must_not_include: la respuesta NO debe contener NINGUNA de estas
    frases.

Es un heurístico de substrings, no un juicio semántico con otro LLM (eso
queda fuera de alcance por ahora) — sirve para detectar regresiones
obvias en fundamentación, anti-alucinación, alcance, idioma y seguridad
cada vez que se cambie rules.md, el prompt, o el modelo.
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

QUESTIONS_PATH = Path(__file__).resolve().parent / "eval_questions.json"


def check_criteria(answer: str, criteria: dict) -> tuple[bool, str]:
    answer_lower = answer.lower()

    must_include_any = criteria.get("must_include_any", [])
    if must_include_any and not any(
        phrase.lower() in answer_lower for phrase in must_include_any
    ):
        return False, f"no contiene ninguna de: {must_include_any}"

    must_not_include = criteria.get("must_not_include", [])
    for phrase in must_not_include:
        if phrase.lower() in answer_lower:
            return False, f"contiene frase prohibida: '{phrase}'"

    return True, "ok"


def run(base_url: str) -> int:
    cases = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    results = []
    with httpx.Client(timeout=60.0) as client:
        for case in cases:
            response = client.post(
                f"{base_url}/v1/responses", json={"input": case["question"]}
            )
            response.raise_for_status()
            body = response.json()
            answer = body["output"][0]["content"][0]["text"]

            passed, reason = check_criteria(answer, case["criteria"])
            results.append(
                {
                    "id": case["id"],
                    "categoria": case["categoria"],
                    "question": case["question"],
                    "answer": answer,
                    "passed": passed,
                    "reason": reason,
                }
            )

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])

    print(f"\n{'=' * 78}")
    print("RESULTADOS DE EVALUACIÓN FUNCIONAL")
    print(f"{'=' * 78}\n")

    for r in results:
        status = "PASÓ" if r["passed"] else "FALLÓ"
        print(f"[{status}] ({r['categoria']}) {r['id']}")
        print(f"  Pregunta:  {r['question']}")
        print(f"  Respuesta: {r['answer']}")
        if not r["passed"]:
            print(f"  Motivo:    {r['reason']}")
        print()

    print(f"{'=' * 78}")
    print(f"RESUMEN: {passed_count}/{total} casos pasaron")
    print(f"{'=' * 78}\n")

    return 0 if passed_count == total else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluación funcional del agente de CV contra un servidor real."
    )
    parser.add_argument(
        "--url", default="http://localhost:8080", help="URL base del servidor"
    )
    args = parser.parse_args()

    sys.exit(run(args.url))


if __name__ == "__main__":
    main()
