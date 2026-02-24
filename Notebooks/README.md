# Sara Notebooks

This directory contains the notebooks used to fine-tune and run inference with the Sara clinical workflow model.

## Fine-Tuning (`Sara.ipynb`)

QLoRA fine-tuning of **google/medgemma-1.5-4b-it** on the [Nadhari/MedToolCalling](https://huggingface.co/datasets/Nadhari/MedToolCalling) dataset (284 samples -- 264 train, 20 eval).

| Parameter | Value |
|---|---|
| Quantization | 4-bit NF4 (BitsAndBytes) |
| LoRA | r=16, alpha=32, dropout=0.05 |
| Max sequence length | 16,384 tokens |
| Hardware | NVIDIA H100 80GB, Flash Attention 2 |
| Trainer | SFTTrainer (TRL) |

A custom data collator handles Gemma 3 `token_type_ids` to mask loss on user/system tokens so the model only learns from assistant responses.

The resulting adapter is merged and pushed to HuggingFace as [Nadhari/Sara-1.5-4B-it](https://huggingface.co/Nadhari/Sara-1.5-4B-it).

## Inference (`Sara_Inference.ipynb`)

Loads **Nadhari/Sara-1.5-4B-it** in bfloat16 and demonstrates the FHIR function-calling format the model was trained on:

- `GET <url>` -- read FHIR resources
- `POST <url> <json-body>` -- create/update FHIR resources
- `FINISH(<answer>)` -- return the final answer

Examples include patient MRN lookup, blood pressure recording, and a multi-turn agent workflow with simulated FHIR server responses.
