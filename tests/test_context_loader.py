"""
Pruebas de app/context_loader.py.

Objetivo: confirmar que load_system_prompt() realmente lee y junta el
contenido de rules.md y de los 5 archivos de cv_data/ (no solo que no
truene), y que @lru_cache evita releer los archivos en cada llamada.
"""

from app.context_loader import load_system_prompt


def test_prompt_incluye_reglas_de_rules_md():
    prompt = load_system_prompt()
    assert "Agente de CV de Karime Trejo Pérez" in prompt


def test_prompt_incluye_contenido_de_los_5_archivos_de_cv_data():
    prompt = load_system_prompt()

    assert "Outlier AI" in prompt  # cv_data/experience.md
    assert "VGG16" in prompt  # cv_data/projects.md
    assert "Tecnológico de Monterrey" in prompt  # cv_data/education.md
    assert "Python" in prompt  # cv_data/skills.md
    assert "karimetrejoperez@gmail.com" in prompt  # cv_data/profile.md


def test_load_system_prompt_esta_cacheado():
    primera_llamada = load_system_prompt()
    segunda_llamada = load_system_prompt()
    assert primera_llamada is segunda_llamada
