"""Time one forward pass of the LLM judge's model on the CPU for each (dtype, threads) pair.

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

biogen-llm-v1's probe measured 189.1 s per judged pair for Qwen2.5-1.5B-Instruct in bfloat16 with
4 torch threads on a 2-CPU limit. This separates the two suspects on the model biogen-llm-v2 uses:
it loads the model once per dtype and times a warm-up plus --passes forward passes of one fixed
prompt (llm_judge's own messages(), with a made-up 250-word passage, no BioGen text) at each
thread count. A configuration whose warm-up takes longer than --cap seconds gets no timed passes.
Standard library apart from main(), so the tests need no torch.

  python bench_dtype.py --model-dir DIR --out FILE [--configs float32:2,bfloat16:2,float32:4,bfloat16:4]
                        [--passes 3 --words 250 --cap 120]
"""
import argparse
import json
import statistics
import sys
import time

import llm_judge

VERSION = "0.1.0"
FILLER = "The trial measured blood pressure in adults over twelve weeks and found no clear change."
SENTENCE = "Drug X lowers blood pressure."


def parse_configs(text):
    """'float32:2,bfloat16:4' -> [('float32', 2), ('bfloat16', 4)]."""
    out = []
    for item in text.split(","):
        dtype, threads = item.strip().split(":")
        if dtype not in llm_judge.DTYPES or int(threads) < 1:
            raise ValueError("bad config %r" % item)
        out.append((dtype, int(threads)))
    return out


def prompt_messages(words=250):
    """llm_judge's messages for a made-up passage of exactly `words` words."""
    filler = FILLER.split()
    passage = " ".join(filler[k % len(filler)] for k in range(words))
    return llm_judge.messages(passage, SENTENCE, words)[0]


def summarize(dtype, threads, times):
    timed = times[1:]
    return {"dtype": dtype, "threads": threads, "warmup_s": times[0], "pass_s": timed,
            "median_s": round(statistics.median(timed), 2) if timed else None}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--configs", default="float32:2,bfloat16:2,float32:4,bfloat16:4")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--words", type=int, default=250)
    ap.add_argument("--cap", type=float, default=120.0)
    a = ap.parse_args(argv)
    configs = parse_configs(a.configs)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model_dir)
    text = tok.apply_chat_template(prompt_messages(a.words), tokenize=False, add_generation_prompt=True)
    enc = tok(text, return_tensors="pt")
    rep = {"version": VERSION, "torch": torch.__version__, "tokens": int(enc["input_ids"].shape[1]),
           "cpu_limit": llm_judge.cpu_limit(), "passes": a.passes, "cap_s": a.cap, "runs": []}
    for dtype in dict.fromkeys(d for d, _ in configs):
        model = AutoModelForCausalLM.from_pretrained(a.model_dir, torch_dtype=getattr(torch, dtype),
                                                     use_safetensors=True, low_cpu_mem_usage=True)
        model.eval()
        for d, threads in configs:
            if d != dtype:
                continue
            torch.set_num_threads(threads)
            times = []
            with torch.inference_mode():
                for _ in range(a.passes + 1):
                    t0 = time.time()
                    model(**enc)
                    times.append(round(time.time() - t0, 2))
                    if times[0] > a.cap:
                        break
            rep["runs"].append(summarize(dtype, threads, times))
            print(json.dumps(rep["runs"][-1]), flush=True)
        del model
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
