# src/backend/sara_model.py
# Deploy Sara-1.5-4B-it on Modal with transformers + FastAPI
# OpenAI-compatible /v1/chat/completions endpoint
#
# Setup:
#   pip install modal
#   modal setup
#   modal secret create huggingface HF_TOKEN=<your-token>
#
# Run:   modal run src/backend/sara_model.py
# Deploy: modal deploy src/backend/sara_model.py

import modal

# --- Config (inlined for Modal deployment) ---
MODEL_NAME = "Nadhari/Sara-1.5-4B-it"
MODEL_REVISION = "main"
MINUTES = 60
GPU_WARM_WINDOW = 60 * MINUTES
REQUEST_TIMEOUT = 10 * MINUTES
SARA_GPU = "A100"
SARA_CONCURRENT_INPUTS = 8

# --- Container image ---
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .uv_pip_install(
        "torch==2.7.0",
        "transformers>=5.0.0",
        "accelerate>=1.5.0",
        "huggingface-hub>=0.30.0",
        "fastapi[standard]>=0.115.0",
        "uvicorn>=0.34.0",
        "sentencepiece>=0.2.0",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

app = modal.App("sara-model")


@app.function(
    image=image,
    gpu=f"{SARA_GPU}:1",
    secrets=[modal.Secret.from_name("huggingface-nadhari")],
    volumes={"/root/.cache/huggingface": hf_cache_vol},
    scaledown_window=GPU_WARM_WINDOW,
    timeout=REQUEST_TIMEOUT,
)
@modal.concurrent(max_inputs=SARA_CONCURRENT_INPUTS)
@modal.web_server(port=8000, startup_timeout=REQUEST_TIMEOUT)
def serve():
    import subprocess
    import sys
    import os

    # Write the FastAPI server as a standalone script
    server_code = r'''
import os
import time
import uuid
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

MODEL_NAME = os.environ.get("MODEL_NAME", "Nadhari/Sara-1.5-4B-it")
MODEL_REVISION = os.environ.get("MODEL_REVISION", "main")

app = FastAPI(title="Sara Model API", version="1.0.0")


# --- Pydantic Models for Request Validation ---
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: list[ChatMessage] = Field(..., min_length=1)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if not v:
            raise ValueError("Messages list cannot be empty")
        return v

# --- Load model at startup ---
from transformers import AutoTokenizer, Gemma3ForConditionalGeneration

print(f"Loading tokenizer: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=MODEL_REVISION)

print(f"Loading model: {MODEL_NAME}")
model = Gemma3ForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    revision=MODEL_REVISION,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
model.eval()
print("Model loaded successfully")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": MODEL_NAME, "object": "model", "owned_by": "user"}],
    }


@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    try:
        # Convert Pydantic models to dicts for tokenizer
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        max_tokens = request.max_tokens
        temperature = request.temperature
        top_p = request.top_p

        input_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
        input_len = inputs["input_ids"].shape[1]

        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "do_sample": temperature > 0,
            "top_p": top_p,
        }
        if temperature > 0:
            gen_kwargs["temperature"] = temperature

        with torch.no_grad():
            outputs = model.generate(**inputs, **gen_kwargs)

        new_tokens = outputs[0][input_len:]
        response_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        completion_tokens = len(new_tokens)

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": input_len,
                "completion_tokens": completion_tokens,
                "total_tokens": input_len + completion_tokens,
            },
        }

    except torch.cuda.OutOfMemoryError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "GPU out of memory. Try reducing max_tokens or message length.",
                    "type": "server_error",
                    "code": "gpu_oom",
                }
            },
        )
    except RuntimeError as e:
        if "CUDA" in str(e) or "cuda" in str(e):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": f"GPU error during inference: {str(e)}",
                        "type": "server_error",
                        "code": "gpu_error",
                    }
                },
            )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Runtime error during inference: {str(e)}",
                    "type": "server_error",
                    "code": "runtime_error",
                }
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Unexpected error during inference: {str(e)}",
                    "type": "server_error",
                    "code": "internal_error",
                }
            },
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    server_path = "/tmp/server.py"
    with open(server_path, "w") as f:
        f.write(server_code)

    env = os.environ.copy()
    env["MODEL_NAME"] = MODEL_NAME
    env["MODEL_REVISION"] = MODEL_REVISION

    subprocess.Popen([sys.executable, server_path], env=env)


# --- Local test entrypoint ---
@app.local_entrypoint()
def main():
    import json

    try:
        import aiohttp
    except ImportError:
        import subprocess as sp

        sp.run(["pip", "install", "aiohttp"], check=True)
        import aiohttp

    import asyncio

    async def test():
        url = serve.get_web_url()
        print(f"\nSara endpoint: {url}")
        print(f"OpenAI base_url: {url}/v1")
        print(f"Model name: {MODEL_NAME}\n")

        async with aiohttp.ClientSession(base_url=url) as session:
            print("Waiting for server to be ready...")
            for attempt in range(120):
                try:
                    async with session.get(
                        "/health", timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            print("Server is healthy!\n")
                            break
                except Exception:
                    pass
                await asyncio.sleep(5)
            else:
                print("Server did not become healthy in time.")
                return

            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "You are an expert in using FHIR functions to assist medical professionals.\n\n"
                            "Question: What's the MRN of the patient with name John Smith "
                            "and DOB of 1985-03-15?"
                        ),
                    }
                ],
                "max_tokens": 256,
                "temperature": 0,
            }

            print("Sending test request...")
            async with session.post(
                "/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                result = await resp.json()
                content = result["choices"][0]["message"]["content"]
                print(f"Response:\n{content}")
                print(f"\nUsage: {json.dumps(result['usage'], indent=2)}")

    asyncio.run(test())
