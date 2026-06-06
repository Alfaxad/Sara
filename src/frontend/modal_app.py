"""Modal deployment for the Sara Next.js frontend.

Deploy:
    modal deploy src/frontend/modal_app.py
"""

from __future__ import annotations

import subprocess
import os

import modal

MINUTES = 60
FRONTEND_PORT = 3000
MODAL_WORKSPACE = os.environ.get("MODAL_WORKSPACE", "nadhari")
FRONTEND_API_URL = os.environ.get(
    "NEXT_PUBLIC_API_URL",
    f"https://{MODAL_WORKSPACE}--sara-for-iris-api.modal.run",
)

image = (
    modal.Image.from_registry("node:22-bookworm-slim", add_python="3.12")
    .workdir("/app")
    .add_local_dir(
        "src/frontend",
        remote_path="/app",
        copy=True,
        ignore=[".next", "node_modules", ".env", ".env.local"],
    )
    .env({"NEXT_PUBLIC_API_URL": FRONTEND_API_URL})
    .run_commands("npm ci", "npm run build")
)

app = modal.App("sara-frontend")


@app.function(
    image=image,
    cpu=1.0,
    memory=2048,
    timeout=10 * MINUTES,
    scaledown_window=15 * MINUTES,
)
@modal.web_server(port=FRONTEND_PORT, startup_timeout=5 * MINUTES)
def serve():
    subprocess.Popen(
        ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", str(FRONTEND_PORT)],
        cwd="/app",
    )
