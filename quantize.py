import torch
import torch.nn as nn
from pathlib import Path
import json

QUANT_TYPES = ["int8", "int4", "none"]

def quantize_linear_int8(module):
    weight = module.weight.data
    scale = weight.abs().max() / 127.0
    if scale == 0:
        scale = 1.0
    q_weight = torch.round(weight / scale).clamp(-128, 127).to(torch.int8)
    return q_weight, scale

def quantize_linear_int4(module):
    weight = module.weight.data
    scale = weight.abs().max() / 7.0
    if scale == 0:
        scale = 1.0
    q_weight = torch.round(weight / scale).clamp(-8, 7).to(torch.int8)
    return q_weight, scale

def dequantize_weight(q_weight, scale, dtype=torch.float32):
    return (q_weight.to(dtype) * scale).to(dtype)

class QuantizedLinear(nn.Module):
    def __init__(self, q_weight, scale, bias=None):
        super().__init__()
        self.register_buffer("q_weight", q_weight)
        self.register_buffer("scale", scale)
        self.register_buffer("bias", bias if bias is not None else torch.zeros(q_weight.shape[0]))
        self.dtype = torch.float32

    def forward(self, x):
        weight = dequantize_weight(self.q_weight, self.scale, x.dtype)
        return nn.functional.linear(x, weight, self.bias)

def quantize_model(model, quant_type="int8"):
    quantized_state = {}
    config = {"quant_type": quant_type, "original_params": sum(p.numel() for p in model.parameters())}

    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and name != "lm_head":
            if quant_type == "int8":
                q_weight, scale = quantize_linear_int8(module)
            elif quant_type == "int4":
                q_weight, scale = quantize_linear_int4(module)
            else:
                continue

            quantized_state[f"{name}.q_weight"] = q_weight
            quantized_state[f"{name}.scale"] = scale
            if module.bias is not None:
                quantized_state[f"{name}.bias"] = module.bias.data

    model_state = model.state_dict()
    for key in model_state:
        if key not in quantized_state and "lm_head" not in key and "token_embed" not in key:
            quantized_state[key] = model_state[key]

    config["quantized_params"] = sum(v.numel() if isinstance(v, torch.Tensor) else 0 for v in quantized_state.values())
    return quantized_state, config

def apply_quantized_model(model, quantized_state, quant_type="int8"):
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear) and name != "lm_head":
            q_weight_key = f"{name}.q_weight"
            scale_key = f"{name}.scale"
            bias_key = f"{name}.bias"

            if q_weight_key in quantized_state and scale_key in quantized_state:
                q_weight = quantized_state[q_weight_key]
                scale = quantized_state[scale_key]
                bias = quantized_state.get(bias_key, None)

                setattr(model, name, QuantizedLinear(q_weight, scale, bias))

    return model

def save_quantized(checkpoint_path, quantized_state, config, output_path=None):
    if output_path is None:
        output_path = Path(checkpoint_path).parent / f"swimegpt_quantized_{config['quant_type']}.pt"

    torch.save({
        "quantized_state_dict": quantized_state,
        "config": config
    }, output_path)

    original_size = Path(checkpoint_path).stat().st_size
    quantized_size = output_path.stat().st_size
    compression = (1 - quantized_size / original_size) * 100

    print(f"Quantized model saved to {output_path}")
    print(f"Original: {original_size / 1e6:.1f} MB | Quantized: {quantized_size / 1e6:.1f} MB | Compression: {compression:.1f}%")
    return output_path

def load_quantized_model(checkpoint_path, model_class, model_config):
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    model = model_class(**model_config)
    quantized_state = checkpoint["quantized_state_dict"]
    config = checkpoint["config"]

    model = apply_quantized_model(model, quantized_state, config["quant_type"])

    for key, value in quantized_state.items():
        if "q_weight" not in key and "scale" not in key and "bias" not in key:
            if key in model.state_dict():
                model.state_dict()[key].copy_(value)

    model.eval()
    return model, config

def quantize_checkpoint(checkpoint_path, quant_type="int8", output_path=None):
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    config = checkpoint["config"]

    from train import SwimeGPT
    model = SwimeGPT(
        vocab_size=config["vocab_size"],
        hidden_dim=config["hidden_dim"],
        num_heads=config["num_heads"],
        num_layers=config["num_layers"],
        max_seq_len=config["max_seq_len"],
        sliding_window=config["sliding_window"]
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    quantized_state, quant_config = quantize_model(model, quant_type)
    quant_config["model_config"] = config

    return save_quantized(checkpoint_path, quantized_state, quant_config, output_path)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python quantize.py <checkpoint_path> <quant_type>")
        print("Quant types: int8, int4")
        sys.exit(1)

    checkpoint_path = sys.argv[1]
    quant_type = sys.argv[2]

    if quant_type not in QUANT_TYPES:
        print(f"Invalid quant type. Choose from: {QUANT_TYPES}")
        sys.exit(1)

    quantize_checkpoint(checkpoint_path, quant_type)
