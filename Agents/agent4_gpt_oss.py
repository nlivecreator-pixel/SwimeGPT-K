"""
Agent 4: GPT OSS 120B Free (via OpenRouter)
Generates comprehensive Russian training data - Batch 2
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
MODEL = "openai/gpt-oss-120b:free"
BASE_URL = "https://openrouter.ai/api/v1"

def generate_batch(batch_id, start_idx, count):
    prompt = f"""Вы генерируете высококачественные обучающие данные на русском языке для языковой модели. Сгенерируйте ровно {count} разнообразных, подробных примеров на русском языке, начиная с индекса {start_idx}.

Каждый пример должен быть богатым, информативным и охватывать следующие темы (чередуйте их):
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

Выведите ТОЛЬКО валидный JSON массив. Каждый объект должен содержать:
- "id": уникальный номер
- "text": подробный текст на русском языке (минимум 3-5 предложений)
- "category": одна из тем выше на русском
- "difficulty": "beginner", "intermediate", или "advanced"

Сделайте контент образовательным, разнообразным и полезным для обучения ИИ-ассистента. НЕ повторяйте контент."""

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
            print(f"Agent 4 Error: {response.status_code} - {response.text}")
            return []

        content = response.json()["choices"][0]["message"]["content"]
        
        start = content.find('[')
        end = content.rfind(']') + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            print(f"Agent 4 (GPT OSS 120B): Generated {len(data)} examples")
            return data
        return []
    except Exception as e:
        print(f"Agent 4 Exception: {e}")
        return []

if __name__ == "__main__":
    batch_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 1000

    data = generate_batch(batch_id, start_idx, count)
    
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    if data:
        output_file = output_dir / f"russian_agent4_batch{batch_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Agent 4: Saved to {output_file}")
    else:
        print("Agent 4: No data generated")
