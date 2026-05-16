import os
import json
import tiktoken
import requests
from pathlib import Path
from typing import List, Dict, Optional

class Tokenizer:
    def __init__(self, vocab_size: int = 32000):
        self.vocab_size = vocab_size
        self.enc = tiktoken.get_encoding("cl100k_base")
        self.eos_id = vocab_size - 1
        self.bos_id = vocab_size - 2
        self.pad_id = 0

    def encode(self, text: str, add_bos: bool = True, add_eos: bool = True) -> List[int]:
        tokens = self.enc.encode(text, allowed_special="all")
        tokens = [t if t < self.vocab_size else 0 for t in tokens]
        if add_bos:
            tokens = [self.bos_id] + tokens
        if add_eos:
            tokens = tokens + [self.eos_id]
        return tokens

    def decode(self, tokens: List[int]) -> str:
        return self.enc.decode(tokens)

    def save(self, path: str):
        data = {"vocab_size": self.vocab_size}
        with open(path, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str) -> 'Tokenizer':
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(vocab_size=data["vocab_size"])


class DataGenerator:
    def __init__(self, api_key_path: str = None):
        if api_key_path is None:
            api_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".openrouter")
        self.api_key_path = api_key_path
        self.api_key = None
        self.load_api_key()

    def load_api_key(self):
        path = Path(self.api_key_path)
        if path.exists():
            self.api_key = path.read_text().strip()
        else:
            raise FileNotFoundError(f"API key file not found: {self.api_key_path}")

    def generate_syntax_data(self, language: str, count: int = 50) -> List[Dict]:
        prompts = {
            "python": f"Generate {count} Python code examples covering: functions, classes, decorators, list/dict comprehensions, generators, context managers, async/await, type hints, dataclasses, exception handling. Output as JSON array with objects containing 'code' and 'description' fields.",
            "typescript": f"Generate {count} TypeScript code examples covering: interfaces, types, generics, enums, decorators, async functions, union types, mapped types, utility types, namespaces, modules. Output as JSON array with objects containing 'code' and 'description' fields.",
            "c++": f"Generate {count} C++ code examples covering: classes, templates, STL containers, smart pointers, RAII, move semantics, lambda expressions, virtual functions, constexpr, namespaces. Output as JSON array with objects containing 'code' and 'description' fields.",
            "russian": f"Generate {count} Russian language examples covering: Cyrillic text, programming terminology in Russian, code comments in Russian, technical documentation in Russian. Output as JSON array with objects containing 'text' and 'description' fields.",
            "english": f"Generate {count} English programming tutorials covering: variable declaration, loops, functions, classes, OOP concepts, data structures, algorithms. Output as JSON array with objects containing 'text' and 'description' fields."
        }

        if language.lower() not in prompts:
            raise ValueError(f"Unsupported language: {language}")

        return self._call_api(prompts[language.lower()])

    def _call_api(self, prompt: str) -> List[Dict]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 8000
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")

        content = response.json()["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise Exception("Failed to parse JSON from API response")

    def save_data(self, language: str, output_path: str):
        data = self.generate_syntax_data(language)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m tools.tokenizer <language> [count]")
        print("Languages: python, typescript, c++, russian, english")
        sys.exit(1)

    language = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    generator = DataGenerator()
    output_file = output_dir / f"{language}_syntax.json"
    generator.save_data(language, str(output_file))
    print(f"Saved {count} examples to {output_file}")


if __name__ == "__main__":
    main()
