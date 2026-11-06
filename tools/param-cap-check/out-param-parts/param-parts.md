Checked 2026-11-06T17:19:55Z.

Parameters in billions. A = every stored tensor; B = A minus vision/audio towers; C = B minus MTP heads; D = C minus per-layer embedding tables. Bold = over the cap of 3,000,000,000.

| Model | Vision | Audio | MTP | Per-layer emb. | A stored | B | C | D | A = HF API |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Qwen/Qwen3.5-0.8B | 0.101 | 0.000 | 0.020 | 0.000 | 0.873 | 0.773 | 0.752 | 0.752 | yes |
| Qwen/Qwen3.5-2B | 0.331 | 0.000 | 0.061 | 0.000 | 2.274 | 1.943 | 1.882 | 1.882 | yes |
| Qwen/Qwen3.5-4B | 0.334 | 0.000 | 0.121 | 0.000 | **4.660** | **4.326** | **4.206** | **4.206** | yes |
| Qwen/Qwen3-0.6B | 0.000 | 0.000 | 0.000 | 0.000 | 0.752 | 0.752 | 0.752 | 0.752 | yes |
| Qwen/Qwen3-1.7B | 0.000 | 0.000 | 0.000 | 0.000 | 2.032 | 2.032 | 2.032 | 2.032 | yes |
| Qwen/Qwen3-4B-Instruct-2507 | 0.000 | 0.000 | 0.000 | 0.000 | **4.022** | **4.022** | **4.022** | **4.022** | yes |
| Qwen/Qwen2.5-1.5B-Instruct | 0.000 | 0.000 | 0.000 | 0.000 | 1.544 | 1.544 | 1.544 | 1.544 | yes |
| Qwen/Qwen2.5-3B-Instruct | 0.000 | 0.000 | 0.000 | 0.000 | **3.086** | **3.086** | **3.086** | **3.086** | yes |
| ibm-granite/granite-3.3-2b-instruct | 0.000 | 0.000 | 0.000 | 0.000 | 2.534 | 2.534 | 2.534 | 2.534 | yes |
| ibm-granite/granite-4.0-1b | 0.000 | 0.000 | 0.000 | 0.000 | 1.632 | 1.632 | 1.632 | 1.632 | yes |
| ibm-granite/granite-4.0-h-1b | 0.000 | 0.000 | 0.000 | 0.000 | 1.462 | 1.462 | 1.462 | 1.462 | yes |
| ibm-granite/granite-4.0-micro | 0.000 | 0.000 | 0.000 | 0.000 | **3.403** | **3.403** | **3.403** | **3.403** | yes |
| ibm-granite/granite-4.0-h-micro | 0.000 | 0.000 | 0.000 | 0.000 | **3.191** | **3.191** | **3.191** | **3.191** | yes |
| ibm-granite/granite-4.1-3b | 0.000 | 0.000 | 0.000 | 0.000 | **3.403** | **3.403** | **3.403** | **3.403** | yes |
| ibm-granite/granite-4.2-3b | 0.000 | 0.000 | 0.000 | 0.000 | **3.660** | **3.660** | **3.660** | **3.660** | yes |
| HuggingFaceTB/SmolLM2-1.7B-Instruct | 0.000 | 0.000 | 0.000 | 0.000 | 1.711 | 1.711 | 1.711 | 1.711 | yes |
| HuggingFaceTB/SmolLM3-3B | 0.000 | 0.000 | 0.000 | 0.000 | **3.075** | **3.075** | **3.075** | **3.075** | yes |
| google/gemma-4-E2B-it | 0.169 | 0.307 | 0.000 | 2.349 | **5.123** | **4.647** | **4.647** | 2.299 | NO (API 5123178051) |
| google/gemma-3-1b-it | - | - | - | - | - | - | - | - | gated (no token used) |
| meta-llama/Llama-3.2-1B-Instruct | - | - | - | - | - | - | - | - | gated (no token used) |
| meta-llama/Llama-3.2-3B-Instruct | - | - | - | - | - | - | - | - | gated (no token used) |
| microsoft/Phi-4-mini-instruct | 0.000 | 0.000 | 0.000 | 0.000 | **3.836** | **3.836** | **3.836** | **3.836** | yes |
| mistralai/Ministral-3-3B-Instruct-2512 | 0.420 | 0.000 | 0.000 | 0.000 | **3.849** | **3.429** | **3.429** | **3.429** | NO (API 3849090048) |
| LiquidAI/LFM2-2.6B | 0.000 | 0.000 | 0.000 | 0.000 | 2.569 | 2.569 | 2.569 | 2.569 | yes |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B | 0.000 | 0.000 | 0.000 | 0.000 | 1.777 | 1.777 | 1.777 | 1.777 | yes |
| allenai/OLMo-2-0425-1B-Instruct | 0.000 | 0.000 | 0.000 | 0.000 | 1.485 | 1.485 | 1.485 | 1.485 | yes |
| tiiuae/Falcon3-3B-Instruct | 0.000 | 0.000 | 0.000 | 0.000 | **3.228** | **3.228** | **3.228** | **3.228** | yes |
