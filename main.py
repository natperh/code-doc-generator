import os

import vertexai

from vertexai.generative_models import GenerativeModel

from google.cloud import secretmanager

from google.oauth2.credentials import Credentials

from googleapiclient.discovery import build


# =====================================================
# CONFIG 
# =====================================================

FOLDER_ID = "1n-FT2x8aS-6WZ2aginmhNJYci3pbrDwi"

PROJECT_ID = "code-doc-generator"

LOCATION = "us-central1"


# =====================================================
# SECRET MANAGER
# =====================================================

def get_secret(secret_name):

    client = secretmanager.SecretManagerServiceClient()

    secret_path = (
        f"projects/{PROJECT_ID}/secrets/"
        f"{secret_name}/versions/latest"
    )

    response = client.access_secret_version(
        request={
            "name": secret_path
        }
    )

    return response.payload.data.decode("utf-8")


# =====================================================
# READ OAUTH DATA
# =====================================================

CLIENT_ID = get_secret(
    "GOOGLE_CLIENT_ID"
)

CLIENT_SECRET = get_secret(
    "GOOGLE_CLIENT_SECRET"
)

REFRESH_TOKEN = get_secret(
    "GOOGLE_REFRESH_TOKEN"
)


# =====================================================
# GOOGLE DOCS AUTH
# =====================================================

creds = Credentials(
    token=None,
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

drive_service = build(
    "drive",
    "v3",
    credentials=creds
)


# =====================================================
# READ PROJECT FILES
# =====================================================

project_files = []

for root, dirs, files in os.walk("."):

    for file in files:

        if file.endswith(".py"):

            path = os.path.join(
                root,
                file
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read()

                project_files.append(
                    f"""
FILE: {path}

{content}
"""
                )

            except Exception:
                pass


code_context = "\n\n".join(
    project_files
)


# =====================================================
# VERTEX AI
# =====================================================

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION
)

model = GenerativeModel(
    "gemini-2.5-pro"
)

prompt = f"""
Analiza el siguiente proyecto.

Genera documentación técnica profesional.

Incluye:

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

Código:

{code_context}
"""

response = model.generate_content(
    prompt
)

documentation = response.text


# =====================================================
# CREATE GOOGLE DOC
# =====================================================

document = docs_service.documents().create(
    body={
        "title": "Documentación Automática"
    }
).execute()

document_id = document["documentId"]

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


# =====================================================
# MOVE DOC TO FOLDER
# =====================================================

file_data = drive_service.files().get(
    fileId=document_id,
    fields="parents"
).execute()

previous_parents = ",".join(
    file_data.get(
        "parents",
        []
    )
)

drive_service.files().update(
    fileId=document_id,
    addParents=FOLDER_ID,
    removeParents=previous_parents,
    fields="id, parents"
).execute()


# =====================================================
# OUTPUT
# =====================================================

print(
    f"Google Doc creado correctamente"
)

print(
    f"https://docs.google.com/document/d/{document_id}/edit"
)
