import os
from pathlib import Path

import vertexai
from vertexai.generative_models import GenerativeModel

# ======================================
# CONFIG
# ======================================

PROJECT_ID = "code-doc-generator"
LOCATION = "us-central1"

# ======================================
# LEER CODIGO
# ======================================

code = Path("calculator.py").read_text(
    encoding="utf-8"
)

# ======================================
# PROMPT
# ======================================

prompt = f"""
Eres un arquitecto de software senior.

Analiza el siguiente proyecto Python.

Genera documentación en Markdown.

Incluye:

# Objetivo

# Funcionalidades

# Dependencias

# Riesgos

# Casos de uso

# Ejemplos

Código:

{code}
"""

# ======================================
# VERTEX
# ======================================

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION
)

model = GenerativeModel(
    "gemini-2.5-pro"
)

response = model.generate_content(
    prompt
)

documentation = response.text

# ======================================
# GUARDAR README
# ======================================

Path("README_GENERATED.md").write_text(
    documentation,
    encoding="utf-8"
)

print("README generado correctamente")
print("Archivo: README_GENERATED.md")
