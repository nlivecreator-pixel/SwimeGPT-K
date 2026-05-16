import torch
import sys
import os
from pathlib import Path

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = GREEN = RED = YELLOW = MAGENTA = BLUE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

COLORS = {
    'user': Fore.CYAN,
    'assistant': Fore.GREEN,
    'error': Fore.RED,
    'info': Fore.YELLOW,
    'system': Fore.MAGENTA,
    'code': Fore.BLUE,
    'reset': Fore.RESET
}

BANNER = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════╗
║  {Fore.GREEN}SwimeGPT-K1.2{Style.RESET_ALL}{Fore.CYAN}                                   ║
║  {Fore.YELLOW}Code Assistant with Sliding Window{Style.RESET_ALL}{Fore.CYAN}         ║
╚═══════════════════════════════════════════════════╝{Style.RESET_ALL}
"""


class SwimeGPTChat:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.messages = []
        self.history = []
        self.config = {
            'max_tokens': 512,
            'temperature': 0.7,
            'top_k': 40,
            'system_prompt': "You are SwimeGPT, a helpful coding assistant. You help with Python, TypeScript, C++, Rust, and can respond in Russian and English. Always provide clear, concise answers with code examples when relevant."
        }

    def print_welcome(self):
        print(BANNER)
        print(f"{COLORS['info']}Type {Fore.WHITE}/help{Style.RESET_ALL}{COLORS['info']} for available commands")
        print(f"{COLORS['info']}Use {Fore.WHITE}'''{COLORS['info']} or {Fore.WHITE}```{COLORS['info']} for multi-line input{Style.RESET_ALL}")
        print()

    def print_help(self):
        help_text = f"""
{COLORS['system']}Available Commands:{COLORS['reset']}
  {Fore.WHITE}/help, /h{Style.RESET_ALL}     - Show this help message
  {Fore.WHITE}/clear, /c{Style.RESET_ALL}    - Clear conversation history
  {Fore.WHITE}/model, /m{Style.RESET_ALL}    - Show model info
  {Fore.WHITE}/system, /s{Style.RESET_ALL}   - Set system prompt
  {Fore.WHITE}/temp <n>{Style.RESET_ALL}     - Set temperature (0.1-2.0)
  {Fore.WHITE}/tokens <n>{Style.RESET_ALL}   - Set max tokens
  {Fore.WHITE}/history{Style.RESET_ALL}      - Show conversation history
  {Fore.WHITE}/exit, /q{Style.RESET_ALL}     - Exit chat
"""
        print(help_text)

    def print_model_info(self):
        params = sum(p.numel() for p in self.model.parameters())
        info = f"""
{COLORS['system']}Model Info:{COLORS['reset']}
  Parameters: {params/1e6:.1f}M
  Vocab Size: {self.model.vocab_size}
  Hidden: {self.model.hidden_dim}
  Max Seq: {self.model.max_seq_len}
  Sliding Window: {self.model.sliding_window if hasattr(self.model, 'sliding_window') else 'N/A'}
"""
        print(info)

    def clear_history(self):
        self.messages = []
        self.history = []
        print(f"{COLORS['info']}Conversation cleared{Style.RESET_ALL}")

    def show_history(self):
        if not self.history:
            print(f"{COLORS['info']}No conversation history{Style.RESET_ALL}")
            return
        for msg in self.history:
            role_color = COLORS.get(msg['role'], '')
            print(f"{role_color}{msg['role'].capitalize()}:{COLORS['reset']} {msg['content'][:100]}...")

    def set_system_prompt(self, prompt):
        self.config['system_prompt'] = prompt
        print(f"{COLORS['info']}System prompt updated{Style.RESET_ALL}")

    def handle_command(self, cmd):
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        commands = {
            '/help': (self.print_help, None),
            '/h': (self.print_help, None),
            '/clear': (self.clear_history, None),
            '/c': (self.clear_history, None),
            '/model': (self.print_model_info, None),
            '/m': (self.print_model_info, None),
            '/history': (self.show_history, None),
            '/exit': (lambda: sys.exit(0), None),
            '/q': (lambda: sys.exit(0), None),
        }

        if command == '/system' or command == '/s':
            if arg:
                self.set_system_prompt(arg)
            else:
                print(f"{COLORS['info']}Current system prompt: {self.config['system_prompt'][:50]}...{Style.RESET_ALL}")
            return True

        if command == '/temp' and arg:
            try:
                temp = float(arg)
                if 0.1 <= temp <= 2.0:
                    self.config['temperature'] = temp
                    print(f"{COLORS['info']}Temperature set to {temp}{Style.RESET_ALL}")
                else:
                    print(f"{COLORS['error']}Temperature must be between 0.1 and 2.0{Style.RESET_ALL}")
            except ValueError:
                print(f"{COLORS['error']}Invalid temperature value{Style.RESET_ALL}")
            return True

        if command == '/tokens' and arg:
            try:
                tokens = int(arg)
                if 1 <= tokens <= 2048:
                    self.config['max_tokens'] = tokens
                    print(f"{COLORS['info']}Max tokens set to {tokens}{Style.RESET_ALL}")
                else:
                    print(f"{COLORS['error']}Tokens must be between 1 and 2048{Style.RESET_ALL}")
            except ValueError:
                print(f"{COLORS['error']}Invalid token count{Style.RESET_ALL}")
            return True

        if command in commands:
            commands[command][0]()
            return True

        return False

    def get_input(self):
        print(f"{COLORS['user']}›{Style.RESET_ALL} ", end="")
        lines = []
        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)

            if line.strip() == '"""' or line.strip() == '```':
                break
            lines.append(line)

        return " ".join(lines).strip()

    def generate_response(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        prompt = self.build_prompt()

        input_ids = torch.tensor([self.tokenizer.encode(prompt)], dtype=torch.long)

        print(f"{COLORS['info']}Generating...{Style.RESET_ALL}", end="\r")

        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                max_new_tokens=self.config['max_tokens'],
                temperature=self.config['temperature'],
                top_k=self.config['top_k']
            )

        response = self.tokenizer.decode(output_ids[0].tolist())
        response = self.extract_response(response, prompt)

        self.messages.append({"role": "assistant", "content": response})
        self.history.extend([{"role": "user", "content": user_input}, {"role": "assistant", "content": response}])

        return response

    def build_prompt(self):
        prompt = f"System: {self.config['system_prompt']}\n\n"
        for msg in self.messages[-10:]:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n\n"
        prompt += "Assistant: "
        return prompt

    def extract_response(self, full_output, prompt):
        if "Assistant:" in full_output:
            return full_output.split("Assistant:")[-1].strip()
        return full_output.replace(prompt, "").strip()

    def format_output(self, text):
        if "```" in text:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    lang = part.split('\n')[0]
                    code = '\n'.join(part.split('\n')[1:])
                    parts[i] = f"{COLORS['code']}{code}{COLORS['reset']}"
            return ''.join(parts)
        return text

    def run(self):
        self.print_welcome()

        while True:
            try:
                user_input = self.get_input()

                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        continue
                    print(f"{COLORS['error']}Unknown command: {user_input}{Style.RESET_ALL}")
                    continue

                if not user_input:
                    continue

                response = self.generate_response(user_input)
                formatted = self.format_output(response)

                print()
                print(f"{COLORS['assistant']}SwimeGPT:{Style.RESET_ALL}")
                for line in formatted.split('\n'):
                    print(f"  {line}")
                print()

            except KeyboardInterrupt:
                print(f"\n{COLORS['info']}Use /exit to quit{Style.RESET_ALL}")
                continue


def load_model(checkpoint_path=None):
    if checkpoint_path is None:
        checkpoint_path = Path(__file__).parent / "model"

    checkpoints = list(Path(checkpoint_path).glob("swimegpt_*.pt"))
    if not checkpoints:
        print(f"{COLORS['error']}No model checkpoint found. Please train the model first.{Style.RESET_ALL}")
        return None

    checkpoint_path = max(checkpoints, key=lambda p: p.stat().st_mtime)

    print(f"{COLORS['info']}Loading model from {checkpoint_path}...{Style.RESET_ALL}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    from train import SwimeGPT, VOCAB_SIZE, HIDDEN_DIM, NUM_HEADS, NUM_LAYERS, MAX_SEQ_LEN, SLIDING_WINDOW

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

    print(f"{COLORS['info']}Model loaded! Config: {checkpoint['config']}{Style.RESET_ALL}")
    return model


def main():
    from tools.tokenizer import Tokenizer

    checkpoint = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        tokenizer = Tokenizer()
    except Exception as e:
        print(f"{COLORS['error']}Tokenizer error: {e}{Style.RESET_ALL}")
        print(f"{COLORS['info']}Make sure tiktoken is installed and .openrouter file exists{Style.RESET_ALL}")
        sys.exit(1)

    model = load_model(checkpoint)

    if model is None:
        sys.exit(1)

    chat = SwimeGPTChat(model, tokenizer)
    chat.run()


if __name__ == "__main__":
    main()