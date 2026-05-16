from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import torch
from pathlib import Path

app = FastAPI(title="SwimeGPT API")

model = None
tokenizer = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    top_k: Optional[int] = 40


class ChatResponse(BaseModel):
    message: str
    model: str = "swimegpt-k1.2"


def load_model():
    global model, tokenizer
    from train import SwimeGPT, VOCAB_SIZE, HIDDEN_DIM, NUM_HEADS, NUM_LAYERS, MAX_SEQ_LEN, SLIDING_WINDOW
    from tools.tokenizer import Tokenizer

    tokenizer = Tokenizer()

    checkpoint_path = Path(__file__).parent / "model"
    checkpoints = list(Path(checkpoint_path).glob("swimegpt_*.pt"))

    if not checkpoints:
        raise RuntimeError("No model checkpoint found")

    checkpoint = torch.load(max(checkpoints, key=lambda p: p.stat().st_mtime), map_location="cpu")

    is_quantized = "quantized_state_dict" in checkpoint

    if is_quantized:
        from quantize import load_quantized_model
        model_config = {
            "vocab_size": VOCAB_SIZE,
            "hidden_dim": HIDDEN_DIM,
            "num_heads": NUM_HEADS,
            "num_layers": NUM_LAYERS,
            "max_seq_len": MAX_SEQ_LEN,
            "sliding_window": SLIDING_WINDOW
        }
        model, quant_config = load_quantized_model(checkpoint_path, SwimeGPT, model_config)
        print(f"SwimeGPT quantized model loaded (type: {quant_config['quant_type']})")
    else:
        model = SwimeGPT(
            vocab_size=VOCAB_SIZE,
            hidden_dim=HIDDEN_DIM,
            num_heads=NUM_HEADS,
            num_layers=NUM_LAYERS,
            max_seq_len=MAX_SEQ_LEN,
            sliding_window=SLIDING_WINDOW
        )
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        print("SwimeGPT model loaded successfully")

    return model, tokenizer


@app.on_event("startup")
async def startup():
    global model, tokenizer
    try:
        model, tokenizer = load_model()
        print("SwimeGPT model loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load model: {e}")


@app.get("/")
async def root():
    return {"status": "ok", "model": "swimegpt-k1.2"}


@app.get("/health")
async def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    system_prompt = "You are SwimeGPT, a helpful coding assistant. Respond in English or Russian."

    prompt = "System: " + system_prompt + "\n\n"
    for msg in request.messages:
        prompt += f"{msg.role.capitalize()}: {msg.content}\n\n"
    prompt += "Assistant: "

    input_ids = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            top_k=request.top_k
        )

    response = tokenizer.decode(output_ids[0].tolist())

    if "Assistant:" in response:
        response = response.split("Assistant:")[-1].strip()

    return ChatResponse(message=response)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)