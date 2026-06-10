from openai import OpenAI
import pandas as pd
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

API_KEY = os.environ.get("")
INPUT_FILE = 'human_corpus.csv'
OUTPUT_FILE = 'step1_bullets_new.jsonl'
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY)
write_lock = threading.Lock()

PROMPT_STEP1 = """The aim here is to reverse-engineer the author's writing process by taking a piece of text from a paper and compressing it into a more concise form. This process simulates how an author might distill their thoughts and key points into a structured, 
yet not overly condensed form. Now as a first step, first summarize the goal of the text, e.g., is it introduction, 
or method, results? and then given a complete piece of text from a paper, reverse-engineer it into a list of bullet points.\n\n"""

def compress_abstract(row):
    attempt = 0
    while attempt < 3:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                max_tokens=500,
                temperature=1.5,
                messages=[{"role": "user", "content": PROMPT_STEP1 + row['abstract']}]
            )
            return {
                'id': row['id'],
                'month': row['month'],
                'original': row['abstract'],
                'bullets': response.choices[0].message.content,
            }
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {row['id']}: {e}")
            time.sleep(5 * (attempt + 1))
            attempt += 1
    return None


def load_done_ids():
    done = set()
    if os.path.exists(OUTPUT_FILE):
        f = open(OUTPUT_FILE)
        for line in f:
            try:
                done.add(json.loads(line)['id'])
            except:
                pass
        f.close()
    return done


df = pd.read_csv(INPUT_FILE, dtype=str)
records = df.to_dict('records')
done_ids = load_done_ids()

new_records = []
for r in records:
    if r['id'] not in done_ids:
        new_records.append(r)
records = new_records

print(f"Already done: {len(done_ids)} | {len(records)}")

ok = 0
fail = 0
with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    futures = {}
    idx = 0
    for row in records:
        future = executor.submit(compress_abstract, row)
        futures[future] = idx
        idx += 1

    processed = 0
    for future in as_completed(futures):
        res = future.result()
        processed += 1
        if res:
            with write_lock:
                fout = open(OUTPUT_FILE, 'a')
                fout.write(json.dumps(res) + '\n')
                fout.flush()
                fout.close()
            ok += 1
        else:
            fail += 1

        if processed % 100 == 0:
            print(f"{processed}/{len(records)} | ok={ok} fail={fail}")

print(f"\nDone. ok={ok} fail={fail}")