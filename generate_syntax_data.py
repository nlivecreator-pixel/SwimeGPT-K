import json
import random
import string

def generate_python_examples(count):
    examples = []
    patterns = [
        ("Function with type hints", "def func_{i}(x: int, y: str = 'default') -> bool:\n    return x > 0 and len(y) > 0"),
        ("Class with methods", "class Class{i}:\n    def __init__(self, value):\n        self.value = value\n    def get_value(self):\n        return self.value"),
        ("List comprehension", "result = [x*{i} for x in range({i}0) if x % 2 == 0]"),
        ("Dict comprehension", "result = {{'key'+str(k): v*{i} for k, v in enumerate(data)}}"),
        ("Decorator", "def decorator{i}(func):\n    def wrapper(*args, **kwargs):\n        return func(*args, **kwargs)\n    return wrapper"),
        ("Lambda", "func = lambda x: x * {i} if x > 0 else x / {i}"),
        ("Generator", "def gen{i}(n):\n    for i in range(n):\n        yield i * {i}"),
        ("Context manager", "class Manager{i}:\n    def __enter__(self):\n        return self\n    def __exit__(self, *args):\n        pass"),
        ("Exception handling", "try:\n    result = {i} / x\nexcept ZeroDivisionError:\n    result = 0"),
        ("Async function", "async def async_func{i}():\n    await asyncio.sleep({i})\n    return {i}"),
    ]
    for i in range(count):
        pattern = random.choice(patterns)
        code = pattern[1].format(i=i)
        examples.append({"code": code, "description": f"{pattern[0]} example {i}"})
    return examples

def generate_typescript_examples(count):
    examples = []
    patterns = [
        ("Interface", "interface Interface{i} {{\n  id: number;\n  name: string;\n  value?: number;\n}}"),
        ("Type alias", "type Type{i} = string | number | boolean;"),
        ("Generic function", "function generic{i}<T>(arg: T): T {{ return arg; }}"),
        ("Enum", "enum Enum{i} {{ Left = 'left', Right = 'right', Up = 'up' }}"),
        ("Class with generics", "class GenericClass{i}<T> {{\n  private value: T;\n  constructor(v: T) {{ this.value = v; }}\n}}"),
        ("Arrow function", "const arrow{i} = (x: number): number => x * {i};"),
        ("Async function", "async function fetch{i}(url: string): Promise<Response> {{ return fetch(url); }}"),
        ("Union type", "type Union{i} = Type{i} | Type{j};"),
        ("Mapped type", "type Mapped{i} = {{ [K in keyof T]: K; }};"),
        ("Decorator", "@decorator{i}\nclass Decorated{i} {{ }}"),
    ]
    for i in range(count):
        pattern = random.choice(patterns)
        j = (i + 1) % count
        code = pattern[1].format(i=i, j=j)
        examples.append({"code": code, "description": f"{pattern[0]} example {i}"})
    return examples

def generate_cpp_examples(count):
    examples = []
    patterns = [
        ("Class definition", "class Class{i} {{\npublic:\n  Class{i}(int v): value(v) {{}}\n  int getValue() const {{ return value; }}\nprivate:\n  int value;\n}};"),
        ("Template function", "template<typename T>\nT max{i}(T a, T b) {{ return a > b ? a : b; }}"),
        ("STL vector", "std::vector<int> vec{i}({i}0, {i});"),
        ("Smart pointer", "std::unique_ptr<int> ptr{i} = std::make_unique<int>({i});"),
        ("Lambda", "auto lambda{i} = [](int x) -> int {{ return x * {i}; }};"),
        ("Move semantics", "void move{i}(std::string&& s) {{ std::string dest = std::move(s); }}"),
        ("RAII", "class Resource{i} {{\npublic:\n  Resource{i}() {{ /* acquire */ }}\n  ~Resource{i}() {{ /* release */ }}\n}};"),
        ("Virtual function", "class Base{i} {{\npublic:\n  virtual void method{i}() = 0;\n}};"),
        ("Constexpr", "constexpr int square{i}(int x) {{ return x * x; }}"),
        ("Namespace", "namespace ns{i} {{ class Inner {{ }}; }}"),
    ]
    for i in range(count):
        pattern = random.choice(patterns)
        code = pattern[1].format(i=i)
        examples.append({"code": code, "description": f"{pattern[0]} example {i}"})
    return examples

def generate_russian_examples(count):
    examples = []
    topics = [
        "программирование", "функция", "класс", "переменная", "цикл",
        "условие", "массив", "словарь", "строка", "число"
    ]
    for i in range(count):
        topic = random.choice(topics)
        text = f"Пример {i}: {topic} в программировании. " + " ".join([f"Термин{j}: определение{j}." for j in range(5)])
        examples.append({"text": text, "description": f"Russian {topic} example {i}"})
    return examples

def generate_english_examples(count):
    examples = []
    topics = [
        "programming", "function", "variable", "loop", "condition",
        "array", "string", "number", "class", "object"
    ]
    for i in range(count):
        topic = random.choice(topics)
        text = f"Example {i}: {topic} in programming. " + " ".join([f"Concept{j}: explanation{j}." for j in range(5)])
        examples.append({"text": text, "description": f"English {topic} tutorial {i}"})
    return examples

if __name__ == "__main__":
    import sys
    import os
    os.makedirs("data", exist_ok=True)

    target_size_mb = 1.0
    avg_chars_per_example = 150
    examples_needed = int(target_size_mb * 1024 * 1024 / avg_chars_per_example)

    print(f"Generating {examples_needed} examples per language...")

    data = generate_python_examples(examples_needed)
    with open("data/python_syntax.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Python: {len(data)} examples")

    data = generate_typescript_examples(examples_needed)
    with open("data/typescript_syntax.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"TypeScript: {len(data)} examples")

    data = generate_cpp_examples(examples_needed)
    with open("data/cplusplus_syntax.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"C++: {len(data)} examples")

    print("Done!")