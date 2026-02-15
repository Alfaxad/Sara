# Modal llms.txt

> Modal is a platform for running Python code in the cloud with minimal
> configuration, especially for serving AI models and high-performance batch
> processing. It supports fast prototyping, serverless APIs, scheduled jobs,
> GPU inference, distributed volumes, and sandboxes.

Important notes:

- Modal's primitives are embedded in Python and tailored for AI/GPU use cases,
  but they can be used for general-purpose cloud compute.
- Modal is a serverless platform, meaning you are only billed for resources used
  and can spin up containers on demand in seconds.

You can sign up for free at [https://modal.com] and get $30/month of credits.

## Docs

- [Introduction](https://modal.com/docs/guide)
- Custom container images
  - [Defining Images](https://modal.com/docs/guide/images.md)
  - [Using existing container images](https://modal.com/docs/guide/existing-images.md)
  - [Fast pull from registry](https://modal.com/docs/guide/fast-pull-from-registry.md)
- GPUs and other resources
  - [GPU acceleration](https://modal.com/docs/guide/gpu.md)
  - [Using CUDA on Modal](https://modal.com/docs/guide/cuda.md)
  - [Reserving CPU and memory](https://modal.com/docs/guide/resources.md)
- Scaling out
  - [Scaling out](https://modal.com/docs/guide/scale.md)
  - [Input concurrency](https://modal.com/docs/guide/concurrent-inputs.md)
  - [Batch processing](https://modal.com/docs/guide/batch-processing.md)
  - [Job queues](https://modal.com/docs/guide/job-queue.md)
  - [Dynamic batching (beta)](https://modal.com/docs/guide/dynamic-batching.md)
  - [Multi-node clusters (beta)](https://modal.com/docs/guide/multi-node-training.md)
- Deployment
  - [Apps, Functions, and entrypoints](https://modal.com/docs/guide/apps.md)
  - [Managing deployments](https://modal.com/docs/guide/managing-deployments.md)
  - [Invoking deployed functions](https://modal.com/docs/guide/trigger-deployed-functions.md)
  - [Continuous deployment](https://modal.com/docs/guide/continuous-deployment.md)
  - [Running untrusted code in Functions](https://modal.com/docs/guide/restricted-access.md)
- Modal Sandboxes
  - [Sandboxes](https://modal.com/docs/guide/sandboxes.md)
  - [Running commands](https://modal.com/docs/guide/sandbox-spawn.md)
  - [Networking and security](https://modal.com/docs/guide/sandbox-networking.md)
  - [File access](https://modal.com/docs/guide/sandbox-files.md)
  - [Snapshots](https://modal.com/docs/guide/sandbox-snapshots.md)
- [Modal Notebooks](https://modal.com/docs/guide/notebooks)
- Secrets and environment variables
  - [Secrets](https://modal.com/docs/guide/secrets.md)
  - [Environment variables](https://modal.com/docs/guide/environment_variables.md)
- [Scheduling and cron jobs](https://modal.com/docs/guide/cron)
- Web endpoints
  - [Web endpoints](https://modal.com/docs/guide/webhooks.md)
  - [Streaming endpoints](https://modal.com/docs/guide/streaming-endpoints.md)
  - [Web endpoint URLs](https://modal.com/docs/guide/webhook-urls.md)
  - [Request timeouts](https://modal.com/docs/guide/webhook-timeouts.md)
  - [Proxy Auth Tokens](https://modal.com/docs/guide/webhook-proxy-auth.md)
- Networking
  - [Tunnels](https://modal.com/docs/guide/tunnels.md)
  - [Proxies (beta)](https://modal.com/docs/guide/proxy-ips.md)
  - [Cluster networking](https://modal.com/docs/guide/private-networking.md)
- Data sharing and storage
  - [Passing local data](https://modal.com/docs/guide/local-data.md)
  - [Volumes](https://modal.com/docs/guide/volumes.md)
  - [Storing model weights](https://modal.com/docs/guide/model-weights.md)
  - [Cloud bucket mounts](https://modal.com/docs/guide/cloud-bucket-mounts.md)
  - [Dicts](https://modal.com/docs/guide/dicts.md)
  - [Queues](https://modal.com/docs/guide/queues.md)
  - [Dataset ingestion](https://modal.com/docs/guide/dataset-ingestion.md)
- Performance
  - [Cold start performance](https://modal.com/docs/guide/cold-start.md)
  - [Memory Snapshot](https://modal.com/docs/guide/memory-snapshot.md)
  - [High-performance LLM inference](https://modal.com/docs/guide/high-performance-llm-inference.md)
  - [Geographic latency](https://modal.com/docs/guide/geographic-latency.md)
- Reliability and robustness
  - [Failures and retries](https://modal.com/docs/guide/retries.md)
  - [Preemption](https://modal.com/docs/guide/preemption.md)
  - [Timeouts](https://modal.com/docs/guide/timeouts.md)
  - [GPU health](https://modal.com/docs/guide/gpu-health.md)
  - [Troubleshooting](https://modal.com/docs/guide/troubleshooting.md)
- [Security and privacy](https://modal.com/docs/guide/security)
- Integrations
  - [Using OIDC to authenticate with external services](https://modal.com/docs/guide/oidc-integration.md)
  - [Connecting Modal to your Datadog account](https://modal.com/docs/guide/datadog-integration.md)
  - [Connecting Modal to your OpenTelemetry provider](https://modal.com/docs/guide/otel-integration.md)
  - [Okta SSO](https://modal.com/docs/guide/okta-sso.md)
  - [Slack notifications (beta)](https://modal.com/docs/guide/slack-notifications.md)
- Workspace & account settings
  - [Workspaces](https://modal.com/docs/guide/workspaces.md)
  - [Environments](https://modal.com/docs/guide/environments.md)
  - [Modal user account setup](https://modal.com/docs/guide/modal-user-account-setup.md)
  - [Service users](https://modal.com/docs/guide/service-users.md)
  - [Billing](https://modal.com/docs/guide/billing.md)
- Other topics
  - [JavaScript/Go SDKs](https://modal.com/docs/guide/sdk-javascript-go.md)
  - [Modal 1.0 migration guide](https://modal.com/docs/guide/modal-1-0-migration.md)
  - [File and project structure](https://modal.com/docs/guide/project-structure.md)
  - [Developing and debugging](https://modal.com/docs/guide/developing-debugging.md)
  - [Developing Modal code with LLMs](https://modal.com/docs/guide/developing-with-llms.md)
  - [Jupyter notebooks](https://modal.com/docs/guide/jupyter-notebooks.md)
  - [Asynchronous API usage](https://modal.com/docs/guide/async.md)
  - [Global variables](https://modal.com/docs/guide/global-variables.md)
  - [Region selection](https://modal.com/docs/guide/region-selection.md)
  - [Container lifecycle hooks](https://modal.com/docs/guide/lifecycle-functions.md)
  - [Parametrized functions](https://modal.com/docs/guide/parametrized-functions.md)
  - [S3 Gateway endpoints](https://modal.com/docs/guide/s3-gateway-endpoints.md)
  - [GPU Metrics](https://modal.com/docs/guide/gpu-metrics.md)

## Examples

- [Featured](https://modal.com/docs/examples)
- Getting started
  - [Hello, world](https://modal.com/docs/examples/hello_world.md)
  - [Simple web scraper](https://modal.com/docs/examples/webscraper.md)
  - [Serving web endpoints](https://modal.com/docs/examples/basic_web.md)
- Large language models (LLMs)
  - [Deploy an OpenAI-compatible LLM service with vLLM](https://modal.com/docs/examples/llm_inference.md)
  - [Cut Ministral 3 cold start times by 10x with snapshots](https://modal.com/docs/examples/ministral3_inference.md)
  - [Maximize tokens per second in batch processing with vLLM](https://modal.com/docs/examples/vllm_throughput.md)
  - [Serve an ultra-low-latency chatbot with SGLang](https://modal.com/docs/examples/sglang_low_latency.md)
  - [Efficient LLM Finetuning with Unsloth](https://modal.com/docs/examples/unsloth_finetune.md)
  - [Run a multimodal RAG chatbot to answer questions about PDFs](https://modal.com/docs/examples/chat_with_pdf_vision.md)
  - [Fine-tune an LLM to replace your CEO](https://modal.com/docs/examples/llm-finetuning.md)
  - [Deploy a stateless MCP with FastMCP](https://modal.com/docs/examples/mcp_server_stateless.md)
- Images, video, & 3D
  - [Edit images with Flux Kontext](https://modal.com/docs/examples/image_to_image.md)
  - [Fine-tune Wan2.1 video models on your face](https://modal.com/docs/examples/music-video-gen.md)
  - [Run Flux fast with torch.compile](https://modal.com/docs/examples/flux.md)
  - [Fine-tune Flux with LoRA](https://modal.com/docs/examples/diffusers_lora_finetune.md)
  - [Animate images with LTX-Video](https://modal.com/docs/examples/image_to_video.md)
  - [Generate video clips with LTX-Video](https://modal.com/docs/examples/ltx.md)
  - [Run Stable Diffusion with a CLI, API, and web UI](https://modal.com/docs/examples/text_to_image.md)
- Audio
  - [Deploy a Moshi voice chatbot](https://modal.com/docs/examples/llm-voice-chat.md)
  - [Stream transcripts at the speed of speech using Kyutai STT](https://modal.com/docs/examples/streaming_kyutai_stt.md)
  - [Make music with ACE-Step](https://modal.com/docs/examples/generate_music.md)
  - [Generate speech with Chatterbox](https://modal.com/docs/examples/chatterbox_tts.md)
  - [Run high throughput batched transcription with Whisper](https://modal.com/docs/examples/batched_whisper.md)
  - [Fine-tune Whisper to recognize new words](https://modal.com/docs/examples/fine_tune_asr.md)
- Real-time communication (WebRTC)
  - [Serverless WebRTC](https://modal.com/docs/examples/webrtc_yolo.md)
  - [WebRTC quickstart with FastRTC](https://modal.com/docs/examples/fastrtc_flip_webcam.md)
- Computational biology
  - [Fold proteins with Chai-1](https://modal.com/docs/examples/chai1.md)
  - [Build a protein-folding dashboard](https://modal.com/docs/examples/esm3.md)
  - [Fold proteins with Boltz-2](https://modal.com/docs/examples/boltz_predict.md)
- Modal Sandboxes
  - [Run a background coding agent with OpenCode](https://modal.com/docs/examples/opencode_server.md)
  - [Build a scalable AI coding platform](https://modal.com/docs/examples/modal-vibe.md)
  - [Run a LangGraph agent's code in a secure GPU sandbox](https://modal.com/docs/examples/agent.md)
  - [Control a sandboxed computer with an LLM](https://modal.com/docs/examples/anthropic_computer_use.md)
  - [Build a stateful, sandboxed code interpreter](https://modal.com/docs/examples/simple_code_interpreter.md)
  - [Run Node.js, Ruby, and more in a Sandbox](https://modal.com/docs/examples/safe_code_execution.md)
  - [Run a sandboxed Jupyter notebook](https://modal.com/docs/examples/jupyter_sandbox.md)
- Reinforcement Learning
  - [Train a model to solve math problems using GRPO and verl](https://modal.com/docs/examples/grpo_verl.md)
  - [Train a model to solve coding problems using GRPO and TRL](https://modal.com/docs/examples/grpo_trl.md)
- Embeddings
  - [Embed millions of documents with TEI](https://modal.com/docs/examples/amazon_embeddings.md)
  - [Turn satellite images into vectors and store them in MongoDB](https://modal.com/docs/examples/mongodb-search.md)
- Parallel processing and job scheduling
  - [Deploy a Hacker News Slackbot](https://modal.com/docs/examples/hackernews_alerts.md)
  - [Run a Document OCR job queue](https://modal.com/docs/examples/doc_ocr_jobs.md)
  - [Serve a Document OCR web app](https://modal.com/docs/examples/doc_ocr_webapp.md)
- Training models from scratch
  - [Train an SLM with early-stopping grid search over hyperparameters](https://modal.com/docs/examples/hp_sweep_gpt.md)
  - [Run long, resumable training jobs](https://modal.com/docs/examples/long-training.md)
- Hosting popular libraries
  - [YOLO: Fine-tune and serve computer vision models](https://modal.com/docs/examples/finetune_yolo.md)
  - [Blender: Build a 3D render farm](https://modal.com/docs/examples/blender_video.md)
  - [Streamlit: Run and deploy Streamlit apps](https://modal.com/docs/examples/serve_streamlit.md)
  - [ComfyUI: Run Flux on ComfyUI as an API](https://modal.com/docs/examples/comfyapp.md)
  - [SQLite: Publish explorable data with Datasette](https://modal.com/docs/examples/cron_datasette.md)
  - [Algolia: Build docsearch with a crawler](https://modal.com/docs/examples/algolia_indexer.md)
- Connecting to other APIs
  - [Discord: Deploy and run a Discord Bot](https://modal.com/docs/examples/discord_bot.md)
  - [Google Sheets: Sync databases and APIs to a Google Sheet](https://modal.com/docs/examples/db_to_sheet.md)
  - [OpenAI: Run a RAG Q&A chatbot](https://modal.com/docs/examples/potus_speech_qanda.md)
  - [Tailscale: Add Modal Apps to your VPN](https://modal.com/docs/examples/modal_tailscale.md)
  - [Prometheus: Publish custom metrics with Pushgateway](https://modal.com/docs/examples/pushgateway.md)
- Managing data
  - [Mount S3 buckets in Modal apps](https://modal.com/docs/examples/s3_bucket_mount.md)
  - [Build your own data warehouse with DuckDB, DBT, and Modal](https://modal.com/docs/examples/dbt_duckdb.md)
  - [Create a LoRA Playground with Modal, Gradio, and S3](https://modal.com/docs/examples/cloud_bucket_mount_loras.md)
- [Miscellaneous](https://modal.com/docs/examples/miscellaneous)

## API Reference

- [Changelog](https://modal.com/docs/reference/changelog)
- [API Reference](https://modal.com/docs/reference)