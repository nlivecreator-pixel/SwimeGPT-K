"""
Agent 3: MiniMax M2.5 Free (via OpenRouter)
Generates comprehensive English training data - Batch 2
"""
import json
import requests
import os
import sys
from pathlib import Path

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not API_KEY:
    key_path = Path(__file__).parent.parent / ".openrouter"
    if key_path.exists():
        API_KEY = key_path.read_text().strip()
MODEL = "minimax/minimax-m2.5:free"
BASE_URL = "https://openrouter.ai/api/v1"

def generate_batch(batch_id, start_idx, count):
    prompt = f"""You are generating high-quality English training data for a language model. Generate exactly {count} diverse, comprehensive English text examples starting from index {start_idx}.

Each example must be rich, informative, and cover these topics (rotate through them):
- Programming concepts and tutorials
- Scientific explanations
- General knowledge and facts
- Technical documentation
- Conversational dialogues
- Problem-solving scenarios
- Code explanations
- Mathematical concepts
- History and culture
- Language learning

Output ONLY a valid JSON array. Each object must have:
- "id": unique number
- "text": rich, detailed English text (at least 3-5 sentences)
- "category": one of the topics above
- "difficulty": "beginner", "intermediate", or "advanced"

Make the content educational, varied, and useful for training an AI assistant. Do NOT repeat content."""

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://swimegpt.local",
                "X-Title": "SwimeGPT-K1.2"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 64000
            },
            timeout=300
        )

        if response.status_code != 200:
            print(f"Agent 3 Error: {response.status_code} - {response.text}")
            return []

        content = response.json()["choices"][0]["message"]["content"]
        
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            print(f"Agent 3 (MiniMax M2.5): Generated {len(data)} examples")
            return data
        return []
    except Exception as e:
        print(f"Agent 3 Exception: {e}")
        return []

if __name__ == "__main__":
    batch_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 1000

    data = generate_batch(batch_id, start_idx, count)
    
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    if data:
        output_file = output_dir / f"english_agent3_batch{batch_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Agent 3: Saved to {output_file}")
    else:
        print("Agent 3: No data generated")
