from fastapi import FastAPI
from pydantic import BaseModel
## ai!!
from typing import Optional
from google import genai
## ai!!
import subprocess
import tempfile
import os
import sys

app = FastAPI()

## ai!!
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None


class CodeRequest(BaseModel):
    code: str

## ai!!
class MistakeRequest(BaseModel):
    question: str
    user_answer: str
    topic: Optional[str] = "Python pamati"


@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}


@app.post("/run-code")
async def run_code(request: CodeRequest):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".py",
            mode="w",
            encoding="utf-8"
        ) as temp_file:
            temp_file.write(request.code)
            temp_path = temp_file.name

        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out.",
            "returncode": -1
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

## ai!!
@app.post("/ai/explain-mistake")
async def explain_mistake(request: MistakeRequest):
    if client is None:
        return {"error": "GEMINI_API_KEY is not set"}

    try:
        prompt = f"""
Tu esi Python programmēšanas valodas pasniedzējs.

Tēma: {request.topic}
Uzdevums: {request.question}
Lietotāja atbilde: {request.user_answer}

Paskaidro īsi latviešu valodā, kāpēc lietotāja atbilde ir nepareiza.
SVARĪGI:
- Nedod pareizo gala atbildi.
- Nepārraksti pilnu risinājumu.
- Neizmanto kodu blokos pilnu pareizo risinājumu.
- Vari dot īsu konceptuālu padomu, ja nav noteikta risinājuma.
- Atbildi 2 līdz 4 teikumos, lai nebūtu daudz jālasa.
- Tonis lai ir skaidrs un atbalstošs, bet ne pārāk draudzīgs, kā pasniedzējam.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {"explanation": response.text.strip() if response.text else ""}

    except Exception as e:
        return {"error": str(e)}
