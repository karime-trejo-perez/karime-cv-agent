# Karime CV Agent — Reto IA Banorte

Agente conversacional encargado de responder preguntas sobre la trayectoria
profesional de Karime Trejo Pérez, a través de un endpoint compatible con
[Open Responses](https://www.openresponses.org/).

**Endpoint desplegado:** `https://karime-cv-agent-129428014758.us-central1.run.app`

---

## 1. Cómo funciona

```
                Plataforma Reto IA Banorte
                (o cualquier cliente HTTP)
                          │
                          ▼
              Google Cloud Run (1 instancia)
                          │
              app/main.py — recibe la pregunta,
              revisa el historial si aplica
                          │
                          ▼
              app/llm.py — le manda a Claude:
              las reglas (rules.md) + el CV
              completo (cv_data/*.md) + la
              pregunta
                          │
                          ▼
              API de Anthropic (claude-haiku-4-5)
```

Cada que un usuario hace una pregunta al agente, el servidor arma un mensaje con: las
reglas de comportamiento del agente, el CV completo, y la pregunta para mandarlo a Claude. La respuesta se guarda para poder continuar la
conversación si hay preguntas de seguimiento.

---

## 2. Decisiones técnicas y justificación

| Decisión | Por qué |
|---|---|
| **Modelo: Claude Haiku** | Es rápido y de bajo costo. Como el agente solo habla de un tema (CV de Karime), no necesita un modelo más robusto ni más costoso. |
| **CV en archivos Markdown, mandado completo en cada pregunta** | El CV completo son ~900 palabras, por lo que cabe sin problema en una sola llamada. Se descartó *tool-calling* al ser un método innecesariamente complicado para un CV tan chico. |
| **FastAPI** | Framework de Python simple, con validación de datos automática (revisa que las preguntas lleguen bien formadas) y documentación interactiva gratis (`/docs`). |
| **Historial de conversación en memoria, limitado a 1 instancia de Cloud Run** | Se decidió que el agente sí recuerde conversaciones (para preguntas de seguimiento), en vez de tratar cada pregunta como aislada. Guardar ese historial en la memoria del servidor es simple, pero si Google levanta más de una copia del servidor a la vez, cada una tiene su propia memoria y no se comparten — esto causó errores reales en pruebas (ver sección 4). Se resolvió limitando a una sola copia del servidor, suficiente para el tráfico bajo que se espera. |
| **Despliegue: Google Cloud Run** | Capa gratuita amplia, se apaga solo cuando nadie lo usa (sin costo en reposo). |
| **La API key vive en Secret Manager, no en el código** | El servidor la consulta en una fuente separada de Google en vez de tenerla escrita en su configuración por razones de seguridad. |
| **Sin filtro extra de seguridad con otro modelo** | Las reglas de comportamiento (`rules.md`) ya cubren lo necesario para un agente de un solo tema, sin acciones de escritura. Agregar otro modelo "vigilante" costaría más sin aportar mucho. |

---

## 3. Pruebas y validación

- **`tests/`** — 8 pruebas automáticas que revisan la funcionalidad del código (lectura del CV correcta, 
respuesta adecuada a preguntas y errores), sin necesidad de hacer llamados a Claude (únicamente pruebas locales).
  ```
  python -m pytest tests/ -v
  ```
- **`eval/`** — 9 preguntas reales contra el agente, revisando que
  responda correctamente sobre la experiencia de Karime, sin inventar datos,
  y redirigiendo preguntas fuera de tema, así como respetando el idioma permitido, y resistiendo intentos de manipulación para revelar el system prompt.
  ```
  python -m eval.run_eval --url http://localhost:8080
  ```

---

## 4. Hallazgos y correcciones durante el desarrollo

- El SDK de Anthropic cambió de versión a mitad del desarrollo y dejó de
  aceptar un parámetro que ya usábamos (`temperature`) de la forma
  original. Se ajustó el código para seguir implementando este parámetro.
- El agente, al ver que el CV menciona que Karime habla alemán, decidió
  por su cuenta responder en alemán a una pregunta en ese idioma, aunque
  la regla decía que solo debía responder en español o inglés. Se corrigió
  aclarando explícitamente que esa regla aplica siempre, sin excepciones.
- Al probar conversaciones con seguimiento contra el agente ya desplegado,
  algunas fallaban de forma intermitente — la causa fue la limitación de
  memoria entre instancias descrita arriba, ya resuelta.

---

## 5. Medidas de seguridad

- Tope de gasto mensual de $5 USD en la cuenta de Anthropic.
- Límite de 6,000 caracteres por pregunta, para evitar que algún usuario mande
  textos enormes y genere un gasto desproporcionado.
- Tiempo máximo de espera de 30 segundos por respuesta de Claude.
- La API key nunca está en el código ni en configuración visible.

---

## 6. Correrlo localmente

```bash
git clone <url-de-este-repo>
cd karime-cv-agent
cp .env.example .env
# pon tu ANTHROPIC_API_KEY real en .env

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8080
```

Probar:
```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "¿Cuál es tu experiencia con evaluación de LLMs?"}'
```

---

## 7. Desplegar en Google Cloud Run

```bash
gcloud config set project TU_PROJECT_ID
gcloud services enable run.googleapis.com secretmanager.googleapis.com

gcloud secrets create anthropic-api-key --data-file=- <<< "sk-ant-..."

gcloud run deploy karime-cv-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --max-instances=1 \
  --set-env-vars ANTHROPIC_MODEL=claude-haiku-4-5 \
  --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest
```

---

## 8. Estructura del proyecto

```
karime-cv-agent/
├── cv_data/        # El CV, en 5 archivos Markdown
├── rules.md         # Reglas de comportamiento del agente
├── app/
│   ├── main.py        # Recibe las preguntas, arma las respuestas
│   ├── llm.py           # Habla con Claude
│   ├── context_loader.py # Lee rules.md + cv_data/*.md
│   ├── schemas.py          # Define qué forma debe tener cada petición
│   ├── store.py              # Guarda el historial de conversación
│   └── logging_config.py      # Registro de actividad del servidor
├── tests/            # Pruebas automáticas del código
├── eval/              # Pruebas de calidad de las respuestas
├── Dockerfile
└── requirements.txt
```