import os
from google.cloud import secretmanager
import vertexai
from vertexai.generative_models import GenerativeModel

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ==================================================
# CONFIGURACION
# ==================================================

PROJECT_ID = "code-doc-generator"
LOCATION = "us-central1"

SOURCE_FOLDER = "sample_project"


# ==================================================
# SECRET MANAGER
# ==================================================

def get_secret(secret_name):

    client = secretmanager.SecretManagerServiceClient()

    name = (
        f"projects/{PROJECT_ID}"
        f"/secrets/{secret_name}"
        f"/versions/latest"
    )

    response = client.access_secret_version(
        request={"name": name}
    )

    return response.payload.data.decode("UTF-8")


# ==================================================
# OAUTH
# ==================================================

CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = get_secret("GOOGLE_REFRESH_TOKEN")

creds = Credentials(
    None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=[
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive"
    ]
)

docs_service = build(
    "docs",
    "v1",
    credentials=creds
)


# ==================================================
# LEER PROYECTO
# ==================================================

project_files = []

for root, dirs, files in os.walk(SOURCE_FOLDER):

    for file in files:

        if not file.endswith(".py"):
            continue

        full_path = os.path.join(root, file)

        try:

            with open(
                full_path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

                project_files.append(
                    f"""
ARCHIVO:
{full_path}

CODIGO:
{content}
"""
                )

        except Exception as e:

            print(
                f"Error leyendo {full_path}: {e}"
            )

print(
    f"Archivos encontrados: {len(project_files)}"
)

code_context = "\n\n".join(project_files)


# ==================================================
# VERTEX AI
# ==================================================

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION
)

model = GenerativeModel("gemini-2.5-pro")

prompt = f"""
Analiza este proyecto Python.

Genera documentación profesional con:

1. Objetivo
2. Arquitectura
3. Componentes
4. Dependencias
5. APIs
6. Servicios
7. Reglas de negocio
8. Diccionario de datos
9. Riesgos
10. Recomendaciones
11. Flujo principal
12. Resumen ejecutivo

Codigo:

{code_context}
"""

response = model.generate_content(prompt)


# ==================================================
# EXTRAER RESPUESTA GEMINI
# ==================================================

documentation = ""

for candidate in response.candidates:

    if not candidate.content.parts:
        continue

    for part in candidate.content.parts:

        if hasattr(part, "text"):

            documentation += part.text


print(
    f"Documentación generada: "
    f"{len(documentation)} caracteres"
)


# ==================================================
# CREAR GOOGLE DOC
# ==================================================

document = docs_service.documents().create(
    body={
        "title": "Documentacion Automatica"
    }
).execute()

document_id = document["documentId"]

print(
    f"Documento creado: {document_id}"
)

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

print("Contenido insertado")


# ==================================================
# URL FINAL
# ==================================================

print(
    "\nDocumento generado:\n"
)

print(
    f"https://docs.google.com/document/d/{document_id}/edit"
)
