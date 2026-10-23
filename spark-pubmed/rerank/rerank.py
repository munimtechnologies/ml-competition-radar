"""Stage-2 reranker for SPARK PubMed/PMC Task 1: a cross-encoder over (question, title + abstract).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

Wraps a local Hugging Face sequence-classification model (planned: NCBI's MedCPT cross-encoder,
public domain, fetched by fetch_model.py) for CPU use: fixed thread count, batches sorted by
length so padding stays small, optional dynamic int8 quantisation of the Linear layers. Scores
match the model card's own call (tokenizer(pairs, truncation=True, padding=True,
max_length=512)) up to float rounding; batching does not change a pair's score.
"""
import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

VERSION = "0.1.0"


def doc_text(title, abstract):
    """One string per article, title then abstract, as in the MedCPT card example."""
    title = (title or "").strip()
    abstract = (abstract or "").strip()
    return (title + " " + abstract).strip()


class CrossEncoder:
    def __init__(self, model_dir, max_length=512, batch_size=8, threads=2, quantize=False):
        torch.set_num_threads(threads)
        self.max_length = max_length
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()
        if quantize:
            self.quantize()

    def quantize(self):
        """Dynamic int8 weights for every nn.Linear, in place (activations stay float)."""
        torch.ao.quantization.quantize_dynamic(self.model, {torch.nn.Linear}, dtype=torch.qint8,
                                               inplace=True)

    def _logits(self, pairs):
        enc = self.tokenizer(pairs, truncation=True, padding=True, return_tensors="pt",
                             max_length=self.max_length)
        with torch.no_grad():
            return self.model(**enc).logits.squeeze(dim=1).tolist()

    def score(self, query, docs):
        """One float per doc, in the docs' order. Higher = more relevant."""
        if not docs:
            return []
        lens = [len(self.tokenizer.tokenize(d)) for d in docs]
        order = sorted(range(len(docs)), key=lambda i: lens[i])
        out = [0.0] * len(docs)
        for s in range(0, len(order), self.batch_size):
            idx = order[s:s + self.batch_size]
            for i, v in zip(idx, self._logits([[query, docs[i]] for i in idx])):
                out[i] = float(v)
        return out

    def rerank(self, query, candidates, k=5):
        """candidates: list of (id, text). Returns [(id, score)] best first, ties keep input order."""
        t0 = time.time()
        scores = self.score(query, [t for _, t in candidates])
        ranked = sorted(range(len(candidates)), key=lambda i: (-scores[i], i))
        self.last_seconds = time.time() - t0
        return [(candidates[i][0], scores[i]) for i in ranked[:k]]
