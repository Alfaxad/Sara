# sara_modal.py
# Deploy Sara-1.5-4B-it on Modal with transformers + FastAPI
# OpenAI-compatible /v1/chat/completions endpoint
#
# Setup:
#   pip install modal
#   modal setup
#   modal secret create huggingface HF_TOKEN=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
#
# Run:   modal run sara_modal.py
# Deploy: modal deploy sara_modal.py

import modal

MINUTES = 60

MODEL_NAME = "Alfaxad/Sara-1.5-4B-it"
MODEL_REVISION = "main"

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

app = modal.App("sara-inference")


@app.function(
    image=image,
    gpu="H100:1",
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/root/.cache/huggingface": hf_cache_vol},
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=10 * MINUTES)
def serve():
    import subprocess, sys, os, json

    # Write the FastAPI server as a standalone script
    server_code = r'''
import os, time, uuid, torch, uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

MODEL_NAME = os.environ.get("MODEL_NAME", "Alfaxad/Sara-1.5-4B-it")
MODEL_REVISION = os.environ.get("MODEL_REVISION", "main")

app = FastAPI()

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
def chat_completions(request: dict):
    messages = request.get("messages", [])
    max_tokens = request.get("max_tokens", 256)
    temperature = request.get("temperature", 0.0)
    top_p = request.get("top_p", 1.0)

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
                    async with session.get("/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
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