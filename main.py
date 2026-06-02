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

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

credentials, _ = default()

drive_service = build(
    "drive",
    "v3",
    credentials=credentials
)

file_metadata = {
    "name": "prueba.txt",
    "parents": ["1n-FT2x8aS-6WZ2aginmhNJYci3pbrDwi"]
}

media = MediaInMemoryUpload(
    b"Hola desde Cloud Build",
    mimetype="text/plain"
)

file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id"
).execute()

print("Archivo creado:", file["id"])
