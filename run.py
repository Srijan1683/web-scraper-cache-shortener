from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent
    venv_python = project_root / ".venv" / "bin" / "python"

    if not venv_python.exists():
        print("Virtual environment not found at .venv/bin/python")
        print("Create it with: python3 -m venv .venv")
        return 1

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(project_root) if not existing_pythonpath else f"{project_root}:{existing_pythonpath}"

    command = [
        str(venv_python),
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    return subprocess.call(command, cwd=project_root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
