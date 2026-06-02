import os
import vertexai

from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from vertexai.generative_models import GenerativeModel

# ==========================================
# CONFIG
# ==========================================

PROJECT_ID = "code-doc-generator"
LOCATION = "us-central1"

FOLDER_ID = "TU_FOLDER_ID"

# ==========================================
# SECRET MANAGER
# ==========================================

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


CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = get_secret("GOOGLE_REFRESH_TOKEN")

# ==========================================
# GOOGLE AUTH
# ==========================================

creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=[
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ],
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

# ==========================================
# VERTEX AI
# ==========================================

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION
)

model = GenerativeModel("gemini-2.5-pro")

# ==========================================
# READ PROJECT FILES
# ==========================================

project_files = []

for root, dirs, files in os.walk("."):

    if ".git" in root:
        continue

    if "venv" in root:
        continue

    if "__pycache__" in root:
        continue

    for file in files:

        if not file.endswith(".py"):
            continue

        path = os.path.join(root, file)

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()

            project_files.append(
                f"\n\n### FILE: {path}\n\n{content}"
            )

        except Exception as e:
            print(f"Error leyendo {path}: {e}")

code_context = "\n".join(project_files)

print(f"Archivos encontrados: {len(project_files)}")

# ==========================================
# PROMPT
# ==========================================

prompt = f"""
Analiza el siguiente proyecto Python.

Genera una documentación profesional con:

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

# ==========================================
# GEMINI RESPONSE
# ==========================================

response = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 8192,
    },
)

def extract_text(response):

    result = ""

    if not response.candidates:
        return result

    for candidate in response.candidates:

        if not candidate.content:
            continue

        for part in candidate.content.parts:

            try:
                if hasattr(part, "text"):
                    result += part.text
            except:
                pass

    return result

documentation = extract_text(response)

print(
    f"Documentación generada: "
    f"{len(documentation)} caracteres"
)

# ==========================================
# CREATE GOOGLE DOC
# ==========================================

document = docs_service.documents().create(
    body={
        "title": "Documentación Automática"
    }
).execute()

document_id = document["documentId"]

print("Documento creado:")
print(document_id)

# ==========================================
# INSERT CONTENT
# ==========================================

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

# ==========================================
# MOVE TO FOLDER
# ==========================================

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
    fields="id, parents",
).execute()

# ==========================================
# RESULT
# ==========================================

doc_url = (
    f"https://docs.google.com/document/d/"
    f"{document_id}/edit"
)

print()
print("===================================")
print("DOCUMENTO GENERADO")
print("===================================")
print(doc_url)
print("===================================")
