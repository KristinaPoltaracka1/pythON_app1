from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import tempfile
import os
import sys

app = FastAPI()


class CodeRequest(BaseModel):
    code: str


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
