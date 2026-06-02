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

FOLDER_ID = "1n-FT2x8aS-6WZ2aginmhNJYci3pbrDwi"

credentials, _ = default()

docs_service = build(
    "docs",
    "v1",
    credentials=credentials
)

drive_service = build(
    "drive",
    "v3",
    credentials=credentials
)

# Crear documento
document = docs_service.documents().create(
    body={
        "title": "Calculator Documentation"
    }
).execute()

document_id = document["documentId"]

# Insertar contenido
docs_service.documents().batchUpdate(
    documentId=document_id,
    body={
        "requests": [
            {
                "insertText": {
                    "location": {
                        "index": 1
                    },
                    "text": documentation
                }
            }
        ]
    }
).execute()

# Mover a carpeta
file = drive_service.files().get(
    fileId=document_id,
    fields="parents"
).execute()

previous_parents = ",".join(
    file.get("parents", [])
)

drive_service.files().update(
    fileId=document_id,
    addParents=FOLDER_ID,
    removeParents=previous_parents,
    fields="id, parents"
).execute()

print(
    f"Google Doc creado: https://docs.google.com/document/d/{document_id}/edit"
)

print("README generado correctamente")
print("Archivo: README_GENERATED.md")
