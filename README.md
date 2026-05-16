# SwimeGPT-K1.2

A lightweight, CPU-friendly code assistant language model built with PyTorch. Features custom sliding window attention, multi-language code understanding (Python, TypeScript, C++), and bilingual support (English/Russian).

## Features

- **Sliding Window Attention** — efficient attention mechanism reducing memory from O(n²) to O(n·w)
- **Multi-Language Code Support** — trained on Python, TypeScript, and C++ examples
- **Bilingual** — understands and responds in English and Russian
- **CPU-Friendly** — ~100M parameters, runs on low-end hardware (Celeron 4205U compatible)
- **Interactive Chat CLI** — colorized terminal interface with slash commands
- **REST API Server** — FastAPI-based server with OpenAI-compatible chat endpoint
- **Synthetic Data Generation** — built-in tool to generate training data via OpenRouter API

## Architecture

| Parameter | Value |
|---|---|
| Vocabulary Size | 32,000 (cl100k_base) |
| Hidden Dimension | 1,024 |
| Attention Heads | 16 |
| Transformer Layers | 22 |
| Sliding Window | 1,024 |
| Max Sequence Length | 2,048 |
| Parameters | ~100M |

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Setup API Key

Create a `.openrouter` file in the project root with your [OpenRouter](https://openrouter.ai) API key:

```bash
echo "your-api-key-here" > .openrouter
```

### 1. Generate Training Data

Generate synthetic code examples using LLMs via OpenRouter:

```bash
python -m tools.tokenizer python 50
python -m tools.tokenizer typescript 50
python -m tools.tokenizer c++ 50
python -m tools.tokenizer russian 50
python -m tools.tokenizer english 50
```

This produces JSON files in the `data/` directory with code examples and descriptions.

### 2. Train the Model

```bash
python train.py data
```

Checkpoints are saved to `model/swimegpt_epoch{N}.pt`.

### 3. Chat with the Model

```bash
python chat.py
```

Interactive CLI with colorized output and built-in commands:

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/model` | Show model info |
| `/system <prompt>` | Set system prompt |
| `/temp <0.1-2.0>` | Set temperature |
| `/tokens <n>` | Set max output tokens |
| `/history` | Show conversation history |
| `/exit` | Quit chat |

### 4. Run API Server

```bash
python api.py
```

Server starts at `http://localhost:8000`. Test it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Write a Python function to reverse a string"}]}'
```

## Project Structure

```
SwimeGPT-K1.2/
├── train.py                  # Training script with SwimeGPT model
├── chat.py                   # Interactive chat CLI
├── api.py                    # FastAPI REST server
├── generate_syntax_data.py   # Standalone data generation script
├── requirements.txt          # Python dependencies
├── tools/
│   ├── tokenizer.py          # Tokenizer + DataGenerator (OpenRouter)
│   ├── coordinator.py        # Multi-agent coordination
│   ├── agent1_mistral_medium.py
│   ├── agent2_mistral_small.py
│   ├── agent3_minimax.py
│   ├── agent4_gpt_oss.py
│   └── agent5_nemotron.py
├── data/                     # Training datasets (JSON)
│   ├── python_syntax.json
│   ├── typescript_syntax.json
│   ├── c++_syntax.json
│   ├── russian_full.json
│   └── english_full.json
└── model/                    # Saved checkpoints
    ├── swimegpt_epoch1.pt
    └── ...
```

## Scaling Up

For a larger model (~400M+ params), modify these constants in `train.py`:

```python
HIDDEN_DIM = 2048
NUM_LAYERS = 36
```

## Hardware Requirements

- **Minimum**: CPU with 4GB RAM (Celeron 4205U or equivalent)
- **Recommended**: GPU with 4GB VRAM (CUDA-enabled) for faster training
- **Training time**: Several hours on CPU, minutes on GPU

## License

MIT
