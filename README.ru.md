# SwimeGPT-K1.2

Лёгкая языковая модель-ассистент для работы с кодом на PyTorch. Собственный механизм скользящего окна, поддержка нескольких языков программирования (Python, TypeScript, C++) и двуязычный интерфейс (русский/английский).

## Возможности

- **Скользящее окно внимания** — эффективный механизм, снижающий потребление памяти с O(n²) до O(n·w)
- **Мультиязычный код** — обучение на примерах Python, TypeScript и C++
- **Двуязычность** — понимает и отвечает на русском и английском
- **Работает на CPU** — ~100M параметров, запускается на слабом железе (совместим с Celeron 4205U)
- **Интерактивный чат** — терминальный интерфейс с подсветкой и slash-командами
- **REST API сервер** — FastAPI-сервер с OpenAI-совместимым эндпоинтом `/chat`
- **Генерация данных** — встроенный инструмент для создания обучающих данных через OpenRouter API

## Архитектура

| Параметр | Значение |
|---|---|
| Размер словаря | 32 000 (cl100k_base) |
| Скрытый размер | 1 024 |
| Головки внимания | 16 |
| Слои трансформера | 22 |
| Скользящее окно | 1 024 |
| Макс. длина последовательности | 2 048 |
| Параметры | ~100M |

## Быстрый старт

### Установка

```bash
pip install -r requirements.txt
```

### Настройка API-ключа

Создайте файл `.openrouter` в корне проекта с вашим ключом от [OpenRouter](https://openrouter.ai):

```bash
echo "your-api-key-here" > .openrouter
```

### 1. Генерация обучающих данных

Создайте синтетические примеры кода через LLM:

```bash
python -m tools.tokenizer python 50
python -m tools.tokenizer typescript 50
python -m tools.tokenizer c++ 50
python -m tools.tokenizer russian 50
python -m tools.tokenizer english 50
```

Результат — JSON-файлы в директории `data/`.

### 2. Обучение модели

```bash
python train.py data
```

Чекпоинты сохраняются в `model/swimegpt_epoch{N}.pt`.

### 2.5. Квантование модели (опционально)

Уменьшите размер модели для ускорения инференса и снижения потребления памяти:

```bash
# INT8 квантование (~4x меньше, минимальная потеря качества)
python quantize.py model/swimegpt_epoch1.pt int8

# INT4 квантование (~8x меньше, умеренная потеря качества)
python quantize.py model/swimegpt_epoch1.pt int4
```

Квантованные модели сохраняются как `model/swimegpt_quantized_int8.pt` или `int4.pt` и автоматически работают с `chat.py` и `api.py`.

### 3. Чат с моделью

```bash
python chat.py
```

Интерактивный CLI с цветовым выделением и встроенными командами:

| Команда | Описание |
|---|---|
| `/help` | Показать справку |
| `/clear` | Очистить историю |
| `/model` | Информация о модели |
| `/system <prompt>` | Установить системный промпт |
| `/temp <0.1-2.0>` | Установить температуру |
| `/tokens <n>` | Макс. количество токенов |
| `/history` | Показать историю |
| `/exit` | Выйти |

### 4. Запуск API сервера

```bash
python api.py
```

Сервер запустится на `http://localhost:8000`. Проверка:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Напиши функцию на Python для переворота строки"}]}'
```

## Структура проекта

```
SwimeGPT-K1.2/
├── train.py                  # Скрипт обучения, модель SwimeGPT
├── chat.py                   # Интерактивный чат CLI
├── api.py                    # REST сервер на FastAPI
├── quantize.py               # Квантование модели (INT8/INT4)
├── generate_syntax_data.py   # Отдельный скрипт генерации данных
├── requirements.txt          # Зависимости Python
├── tools/
│   ├── tokenizer.py          # Токенизатор + DataGenerator (OpenRouter)
│   ├── coordinator.py        # Координация мульти-агентов
│   ├── agent1_mistral_medium.py
│   ├── agent2_mistral_small.py
│   ├── agent3_minimax.py
│   ├── agent4_gpt_oss.py
│   └── agent5_nemotron.py
├── data/                     # Обучающие датасеты (JSON)
│   ├── python_syntax.json
│   ├── typescript_syntax.json
│   ├── c++_syntax.json
│   ├── russian_full.json
│   └── english_full.json
└── model/                    # Сохранённые чекпоинты
    ├── swimegpt_epoch1.pt
    └── ...
```

## Масштабирование

Для более крупной модели (~400M+ параметров) измените константы в `train.py`:

```python
HIDDEN_DIM = 2048
NUM_LAYERS = 36
```

## Требования к железу

- **Минимум**: CPU, 4 ГБ ОЗУ (Celeron 4205U или аналог)
- **Рекомендуется**: GPU с 4 ГБ VRAM (CUDA) для ускорения обучения
- **Время обучения**: несколько часов на CPU, минуты на GPU

## Лицензия

MIT
