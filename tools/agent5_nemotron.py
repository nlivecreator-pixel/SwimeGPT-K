"""
Agent 5: Nemotron Nano (via OpenRouter)
Generates bilingual English/Russian training data - Batch 3
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
MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
BASE_URL = "https://openrouter.ai/api/v1"

def generate_batch(batch_id, start_idx, count, language="english"):
    if language == "russian":
        prompt = f"""Вы генерируете высококачественные обучающие данные на русском языке. Сгенерируйте ровно {count} примеров, начиная с индекса {start_idx}.

Темы (чередуйте):
- Программирование и разработка ПО
- Научные объяснения
- Общие знания и факты
- Техническая документация
- Диалоги и общение
- Сценарии решения проблем
- Объяснения кода
- Математические понятия
- История и культура
- Изучение языков

Выведите ТОЛЬКО валидный JSON массив. Каждый объект:
- "id": уникальный номер
- "text": подробный текст на русском (минимум 3-5 предложений)
- "category": тема на русском
- "difficulty": "beginner", "intermediate", или "advanced"

НЕ повторяйте контент."""
    else:
        prompt = f"""You are generating high-quality English training data. Generate exactly {count} examples starting from index {start_idx}.

Topics (rotate):
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

Output ONLY a valid JSON array. Each object:
- "id": unique number
- "text": rich, detailed English text (at least 3-5 sentences)
- "category": one of the topics above
- "difficulty": "beginner", "intermediate", or "advanced"

Do NOT repeat content."""

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
            print(f"Agent 5 Error: {response.status_code} - {response.text}")
            return []

        content = response.json()["choices"][0]["message"]["content"]
        
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            print(f"Agent 5 (Nemotron Nano): Generated {len(data)} examples ({language})")
            return data
        return []
    except Exception as e:
        print(f"Agent 5 Exception: {e}")
        return []

if __name__ == "__main__":
    batch_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    language = sys.argv[4] if len(sys.argv) > 4 else "english"

    data = generate_batch(batch_id, start_idx, count, language)
    
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    if data:
        output_file = output_dir / f"{language}_agent5_batch{batch_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Agent 5: Saved to {output_file}")
    else:
        print("Agent 5: No data generated")
