"""
Coordinator: Runs all 5 agents simultaneously to generate 25k+ lines per language.
Each agent runs multiple batches in parallel using threading.
"""
import subprocess
import threading
import time
import json
from pathlib import Path

# Configuration: 25000+ examples per language, split across agents
# Agent 1 (Mistral Medium): English batches 0-9 (10 batches x 1000 = 10000)
# Agent 2 (Mistral Small): Russian batches 0-9 (10 batches x 1000 = 10000)
# Agent 3 (MiniMax): English batches 0-7 (8 batches x 1000 = 8000)
# Agent 4 (GPT OSS): Russian batches 0-7 (8 batches x 1000 = 8000)
# Agent 5 (Nemotron): English + Russian batches 0-6 (7 batches x 1000 each = 14000 total)

# Total: ~25000 English, ~25000 Russian

BATCH_SIZE = 1000
ENGLISH_BATCHES_AGENT1 = 10
RUSSIAN_BATCHES_AGENT2 = 10
ENGLISH_BATCHES_AGENT3 = 8
RUSSIAN_BATCHES_AGENT4 = 8
ENGLISH_BATCHES_AGENT5 = 7
RUSSIAN_BATCHES_AGENT5 = 7

def run_agent(script, batch_id, start_idx, count, language=None):
    """Run a single agent batch"""
    cmd = ["python", script, str(batch_id), str(start_idx), str(count)]
    if language:
        cmd.append(language)
    
    print(f"Starting: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd="D:\\SwimeProducts\\SwimeGPT-K1.2")
        print(f"Done: {script} batch {batch_id}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"Timeout: {script} batch {batch_id}")
    except Exception as e:
        print(f"Error: {script} batch {batch_id} - {e}")

def merge_files(pattern, output_file):
    """Merge all JSON files matching pattern into one"""
    all_data = []
    data_dir = Path("D:\\SwimeProducts\\SwimeGPT-K1.2\\data")
    
    for f in data_dir.glob(pattern):
        with open(f, 'r', encoding='utf-8') as fp:
            try:
                data = json.load(fp)
                all_data.extend(data)
                print(f"Merged {f.name}: {len(data)} items")
            except:
                print(f"Failed to merge {f.name}")
    
    # Deduplicate by id
    seen = set()
    unique_data = []
    for item in all_data:
        item_id = item.get('id', None)
        if item_id is not None and item_id not in seen:
            seen.add(item_id)
            unique_data.append(item)
    
    with open(data_dir / output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nMerged {output_file}: {len(unique_data)} unique items")
    return len(unique_data)

def main():
    print("=" * 60)
    print("SwimeGPT-K1.2 Data Generation Coordinator")
    print("=" * 60)
    
    threads = []
    
    # Agent 1: Mistral Medium - English
    for i in range(ENGLISH_BATCHES_AGENT1):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent1_mistral_medium.py", i, i * BATCH_SIZE, BATCH_SIZE
        ))
        threads.append(t)
    
    # Agent 2: Mistral Small - Russian
    for i in range(RUSSIAN_BATCHES_AGENT2):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent2_mistral_small.py", i, i * BATCH_SIZE, BATCH_SIZE
        ))
        threads.append(t)
    
    # Agent 3: MiniMax - English
    for i in range(ENGLISH_BATCHES_AGENT3):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent3_minimax.py", i, i * BATCH_SIZE, BATCH_SIZE
        ))
        threads.append(t)
    
    # Agent 4: GPT OSS - Russian
    for i in range(RUSSIAN_BATCHES_AGENT4):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent4_gpt_oss.py", i, i * BATCH_SIZE, BATCH_SIZE
        ))
        threads.append(t)
    
    # Agent 5: Nemotron - English + Russian
    for i in range(ENGLISH_BATCHES_AGENT5):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent5_nemotron.py", i, i * BATCH_SIZE, BATCH_SIZE, "english"
        ))
        threads.append(t)
    
    for i in range(RUSSIAN_BATCHES_AGENT5):
        t = threading.Thread(target=run_agent, args=(
            "tools/agent5_nemotron.py", i, i * BATCH_SIZE, BATCH_SIZE, "russian"
        ))
        threads.append(t)
    
    print(f"\nLaunching {len(threads)} agent batches in parallel...")
    print("This will take several minutes. Please wait...\n")
    
    start_time = time.time()
    
    # Start all threads
    for t in threads:
        t.start()
        time.sleep(0.5)  # Small delay to avoid rate limiting
    
    # Wait for all to complete
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    print(f"\nAll agents completed in {elapsed:.1f} seconds")
    
    # Merge results
    print("\n" + "=" * 60)
    print("Merging results...")
    print("=" * 60)
    
    en_count = merge_files("english_*.json", "english_full.json")
    ru_count = merge_files("russian_*.json", "russian_full.json")
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"  English examples: {en_count}")
    print(f"  Russian examples: {ru_count}")
    print(f"  Total: {en_count + ru_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
