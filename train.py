import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import json
import math
from pathlib import Path
from typing import Optional
import os

VOCAB_SIZE = 32000
HIDDEN_DIM = 1024
NUM_HEADS = 16
NUM_LAYERS = 22
SLIDING_WINDOW = 1024
MAX_SEQ_LEN = 2048
DROPOUT = 0.1

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


class SwipeAttention(nn.Module):
    def __init__(self, hidden_dim, num_heads, sliding_window):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.sliding_window = sliding_window

        self.qkv = nn.Linear(hidden_dim, hidden_dim * 3)
        self.o_proj = nn.Linear(hidden_dim, hidden_dim)
        self.attn_drop = nn.Dropout(DROPOUT)

    def forward(self, x, mask=None):
        B, T, C = x.shape
        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        if self.sliding_window > 0 and T > self.sliding_window:
            local_attn = torch.ones(T, T, device=x.device)
            local_attn = torch.triu(local_attn, diagonal=-self.sliding_window)
            local_attn = torch.tril(local_attn, diagonal=0)
            attn = attn.masked_fill(local_attn == 0, float('-inf'))

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = torch.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        out = torch.matmul(attn, v).transpose(1, 2).contiguous().reshape(B, T, C)
        return self.o_proj(out)


class SwipeBlock(nn.Module):
    def __init__(self, hidden_dim, num_heads, sliding_window):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.attn = SwipeAttention(hidden_dim, num_heads, sliding_window)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(DROPOUT),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(DROPOUT)
        )

    def forward(self, x, mask=None):
        x = x + self.attn(self.norm1(x), mask)
        x = x + self.mlp(self.norm2(x))
        return x


class SwimeGPT(nn.Module):
    def __init__(self, vocab_size, hidden_dim, num_heads, num_layers, max_seq_len, sliding_window):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_dim = hidden_dim
        self.max_seq_len = max_seq_len

        self.token_embed = nn.Embedding(vocab_size, hidden_dim)
        self.pos_embed = nn.Embedding(max_seq_len, hidden_dim)
        self.drop = nn.Dropout(DROPOUT)

        self.layers = nn.ModuleList([
            SwipeBlock(hidden_dim, num_heads, sliding_window)
            for _ in range(num_layers)
        ])

        self.norm = nn.LayerNorm(hidden_dim)
        self.lm_head = nn.Linear(hidden_dim, vocab_size, bias=False)

        self.token_embed.weight = self.lm_head.weight

    def forward(self, input_ids, targets=None):
        B, T = input_ids.shape
        T = min(T, self.max_seq_len)

        input_ids = input_ids[:, :T]
        if targets is not None:
            targets = targets[:, :T]

        pos = torch.arange(T, device=input_ids.device)
        x = self.drop(self.token_embed(input_ids) + self.pos_embed(pos))

        for layer in self.layers:
            x = layer(x)

        x = self.norm(x)
        logits = self.lm_head(x)

        loss = None
        if targets is not None:
            loss = nn.functional.cross_entropy(
                logits.view(-1, self.vocab_size),
                targets.view(-1),
                ignore_index=-1
            )

        return logits, loss

    @torch.no_grad()
    def generate(self, input_ids, max_new_tokens, temperature=0.7, top_k=None):
        for _ in range(max_new_tokens):
            input_ids_cond = input_ids if input_ids.size(1) <= self.max_seq_len else input_ids[:, -self.max_seq_len:]
            logits, _ = self(input_ids_cond)
            logits = logits[:, -1, :] / temperature

            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float('-inf')

            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_token], dim=1)

            if next_token.item() == 1:
                break

        return input_ids


class CodeDataset(Dataset):
    def __init__(self, data_dir, tokenizer, max_seq_len=MAX_SEQ_LEN):
        self.data = []
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len

        data_path = Path(data_dir)
        if data_path.exists():
            for f in data_path.glob("*.json"):
                with open(f, 'r', encoding='utf-8') as fp:
                    items = json.load(fp)
                    for item in items:
                        if 'code' in item:
                            text = f"{item.get('description', '')}\n{item['code']}"
                        else:
                            text = f"{item.get('description', '')}\n{item.get('text', '')}"
                        self.data.append(text)

        if len(self.data) == 0:
            self.data = ["def hello():\n    print('Hello, World!')"]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        tokens = self.tokenizer.encode(self.data[idx])
        if len(tokens) > self.max_seq_len:
            tokens = tokens[:self.max_seq_len]

        input_ids = torch.tensor(tokens[:-1], dtype=torch.long)
        targets = torch.tensor(tokens[1:], dtype=torch.long)
        return input_ids, targets


class DataCollator:
    def __init__(self, tokenizer, max_seq_len):
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.pad_id = getattr(tokenizer, "pad_id", 0)

    def __call__(self, batch):
        input_ids, targets = zip(*batch)
        input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=self.pad_id)
        targets = torch.nn.utils.rnn.pad_sequence(targets, batch_first=True, padding_value=-1)

        if input_ids.size(1) > self.max_seq_len:
            input_ids = input_ids[:, :self.max_seq_len]
            targets = targets[:, :self.max_seq_len]

        return input_ids, targets


def train_model(data_dir: str, output_dir: str = "model", epochs: int = 3, batch_size: int = 2, lr: float = 1e-4):
    from tools.tokenizer import Tokenizer

    print("Initializing tokenizer...")
    tokenizer = Tokenizer(vocab_size=VOCAB_SIZE)

    print("Loading dataset...")
    dataset = CodeDataset(data_dir, tokenizer)
    print(f"Dataset size: {len(dataset)}")

    collator = DataCollator(tokenizer, MAX_SEQ_LEN)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, collate_fn=collator, num_workers=0)

    print("Initializing model...")
    model = SwimeGPT(
        vocab_size=VOCAB_SIZE,
        hidden_dim=HIDDEN_DIM,
        num_heads=NUM_HEADS,
        num_layers=NUM_LAYERS,
        max_seq_len=MAX_SEQ_LEN,
        sliding_window=SLIDING_WINDOW
    )

    params = count_parameters(model)
    print(f"Model parameters: {params/1e6:.1f}M")

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs * len(dataloader))

    model.train()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Using device: {device}")

    print(f"Starting training for {epochs} epochs...")
    for epoch in range(epochs):
        total_loss = 0
        for batch_idx, (input_ids, targets) in enumerate(dataloader):
            input_ids = input_ids.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            _, loss = model(input_ids, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            if batch_idx % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(dataloader)} | Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1} complete | Avg Loss: {avg_loss:.4f}")

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        torch.save({
            'model_state_dict': model.state_dict(),
            'config': {
                'vocab_size': VOCAB_SIZE,
                'hidden_dim': HIDDEN_DIM,
                'num_heads': NUM_HEADS,
                'num_layers': NUM_LAYERS,
                'max_seq_len': MAX_SEQ_LEN,
                'sliding_window': SLIDING_WINDOW
            }
        }, output_path / f"swimegpt_epoch{epoch+1}.pt")

    print("Training complete!")
    return model


if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    train_model(data_dir)