from openai import OpenAI
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

API_KEY     = ''
INPUT_FILE  = 'step1_bullets_new.jsonl'
OUTPUT_FILE = 'rewritten_abstracts_new.jsonl'
CONCURRENCY = 5

client = OpenAI(api_key=API_KEY)
write_lock = threading.Lock()

def expand_bullets(row):
    attempt = 0
    while attempt < 3:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                max_tokens=500,
                temperature=1.5,
                messages=[{
                    "role": "user",
                    "content": (
                        "Following the initial step of reverse-engineering the author's writing process by compressing "
                        "a text segment from a paper, you now enter the second phase. Here, your objective is to expand upon the concise version previously crafted. "
                        " This stage simulates how an author elaborates on the distilled thoughts and key points, "
                        "enriching them into a detailed, structured narrative. "
                        "Given the concise output from the previous step, your task is to develop it into a fully "
                        "fleshed-out text.\n\n"
                        + row['bullets']
                    )
                }]
            )
            return {
                'id':        row['id'],
                'month':     row['month'],
                'original':  row['original'],
                'rewritten': response.choices[0].message.content
            }
        except Exception as e:
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

records = []
f = open(INPUT_FILE)
for line in f:
    try:
        records.append(json.loads(line))
    except:
        pass
f.close()

done_ids = load_done_ids()

new_records = []
for r in records:
    if r['id'] not in done_ids:
        new_records.append(r)
records = new_records

print(f"Already done: {len(done_ids):,} | Remaining: {len(records):,}")

ok = 0
fail = 0

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    futures = {}
    idx = 0
    for row in records:
        future = executor.submit(expand_bullets, row)
        futures[future] = idx
        idx += 1

    i = 0
    for future in as_completed(futures):
        result = future.result()
        i += 1
        if result:
            with write_lock:
                fout = open(OUTPUT_FILE, 'a')
                fout.write(json.dumps(result) + '\n')
                fout.flush()
                fout.close()
            ok += 1
        else:
            fail += 1
        if i % 100 == 0:
            print(f"  {i}/{len(records)} | ok={ok} fail={fail}")

print(f"\nDone. ok={ok:,} fail={fail:,}")