"""How do MV2's extractive Task 2 answers compare with the 30 TREC 2024 BioGen runs on NLM's
expert nuggets, at the same length?

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

MV2's SPARK Task 2 composer (t2dev-v1, composer 0.2.0) answered all 65 BioGen 2024 questions with
sentences taken whole from PubMed abstracts, about 250 words each, twice as long as the longest
BioGen run. MedAESQA (NLM, CC0) gives expert nuggets for 40 of those questions. This job scores
MV2's answers and the 30 runs against those nuggets with medaesqa_nugget 0.2.0's matcher
(published, fetched at a fixed commit), unchanged:

  matched length  for each run, MV2's answer to each question is cut to that run's own length
                  (content words) and the two are compared on nugget recall at bar 0.6
  fixed budget    every answer cut to 40 content words (20, 60 and the whole answer for
                  sensitivity); MV2's rank among the 31
  ceiling         the best whole sentences chosen from each answer (greedy, knowing the nuggets)
                  within the same length: is the content there, in a different order or mix?
  controls        medaesqa_nugget's own checks (expert answers, shuffled nuggets) recomputed, and
                  MV2's answers against the next question's nuggets

Outputs (counts and scores only, never question, nugget or sentence text):
  mv2_nugget.json   totals, mapping, yardstick checks, matched-length and fixed-budget results
  mv2_systems.json  per run and for MV2: recall per budget, ceiling, words, sentences
Python standard library only; biogen_reuse 0.1.0 and medaesqa_nugget 0.2.0 are imported unchanged.
"""
import argparse
import json
import os
import statistics
import sys
import time

import biogen_reuse as br
import medaesqa_nugget as mn

VERSION = "0.1.0"
NAME = "MV2"
BAR = mn.BAR  # 0.6, medaesqa_nugget's fixed bar
BUDGET = 40  # content words, fixed before any run; BUDGETS are reported for sensitivity only
BUDGETS = (20, 40, 60, None)  # None = the whole answer
HALF = 15  # "beats at least half of the 30 runs"
YARDSTICK_KEYS = ("questions", "runs", "nuggets", "nuggets_per_question", "questions_without_nuggets",
                  "control_expert_recall", "control_shuffled_recall", "sentence_auroc")


def key(budget):
    return "all" if budget is None else str(budget)


def load_mv2(path):
    """{BioGen topic id: [(None, content words), ...]}: each answer's response sentences in order."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                out[str(rec["info_need_id"])] = [(None, br.content(r.get("text"))) for r in rec.get("responses") or []
                                                 if isinstance(r, dict)]
    return out


def words(rows):
    return sum(len(w) for _, w in rows)


def cut(rows, budget):
    """The leading sentences whose content words add up to at most budget; the first sentence is
    always kept unless budget is 0 (a run that gave no answer). None keeps everything."""
    if budget is None:
        return list(rows)
    if budget <= 0:
        return []
    out, n = [], 0
    for lab, w in rows:
        if out and n + len(w) > budget:
            break
        out.append((lab, w))
        n += len(w)
    return out


def recall(rows, nuggets):
    """Share of nuggets covered at >= BAR by one scored sentence (None without nuggets)."""
    return mn.run_scores(rows, nuggets)[0][BAR]


def ceiling(rows, nuggets, budget):
    """Greedy best choice of whole scored sentences from rows, in any order, within budget content
    words: each step adds the sentence covering the most not-yet-covered nuggets at >= BAR (ties:
    fewer words, then earlier). Share of nuggets covered; None without nuggets."""
    if not nuggets:
        return None
    sents = [w for _, w in rows if len(w) >= br.MIN_WORDS]
    covers = [{i for i, n in enumerate(nuggets) if mn.cover(n, s) >= BAR} for s in sents]
    got, used, left = set(), 0, list(range(len(sents)))
    while True:
        best = None
        for j in left:
            if budget is not None and used + len(sents[j]) > budget:
                continue
            rank = (len(covers[j] - got), -len(sents[j]), -j)
            if rank[0] and (best is None or rank > best[0]):
                best = (rank, j)
        if best is None:
            break
        j = best[1]
        got |= covers[j]
        used += len(sents[j])
        left.remove(j)
    return len(got) / len(nuggets)


def map_topics(qmap, mv2, expert, tq):
    """{MedAESQA id: MV2 answer id}: the BioGen id itself when MV2 answered it, else the topics-file
    question with the highest Dice (>= 0.8) against the MedAESQA question."""
    out, how = {}, {"by_id": 0, "by_text": 0, "unmatched": 0, "min_text_dice": None}
    for q, t in sorted(qmap.items()):
        if t in mv2:
            out[q] = t
            how["by_id"] += 1
            continue
        best = max(((br.dice(expert[q]["question"], w), i) for i, w in tq.items() if i in mv2), default=(0.0, None))
        if best[0] >= 0.8:
            out[q] = best[1]
            how["by_text"] += 1
            d = br.r4(best[0])
            how["min_text_dice"] = d if how["min_text_dice"] is None else min(how["min_text_dice"], d)
        else:
            how["unmatched"] += 1
    return out, how


def compare(expert, qmap, data, mv2, tmap):
    """Per system (30 runs and MV2) recall per budget and ceiling; MV2 against each run at that
    run's own length; MV2's rank at each fixed budget."""
    qs = sorted(qmap, key=lambda k: (len(k), k))
    runs = sorted({r for q in qs for r in data[qmap[q]]})
    nug = {q: expert[q]["nuggets"] for q in qs}
    systems = {r: {q: data[qmap[q]].get(r, []) for q in qs} for r in runs}
    systems[NAME] = {q: mv2.get(tmap.get(q), []) for q in qs}
    per = {}
    for s, ans in sorted(systems.items()):
        per[s] = {"sentences_per_question": br.r4(mn.avg([len(ans[q]) for q in qs])),
                  "content_words_per_question": br.r4(mn.avg([words(ans[q]) for q in qs])),
                  "recall": {key(b): mn.pct(mn.avg([recall(cut(ans[q], b), nug[q]) for q in qs])) for b in BUDGETS},
                  "words_at": {key(b): br.r4(mn.avg([words(cut(ans[q], b)) for q in qs])) for b in BUDGETS},
                  "ceiling": {key(b): mn.pct(mn.avg([ceiling(ans[q], nug[q], b) for q in qs])) for b in BUDGETS}}
    me = systems[NAME]
    per[NAME]["shuffled_recall"] = mn.pct(mn.avg([recall(cut(me[q], BUDGET), nug[qs[(i + 1) % len(qs)]])
                                                  for i, q in enumerate(qs)]))
    matched = {}
    for r in runs:
        own = [recall(systems[r][q], nug[q]) for q in qs]
        mine = [recall(cut(me[q], words(systems[r][q])), nug[q]) for q in qs]
        top = [ceiling(me[q], nug[q], words(systems[r][q])) for q in qs]
        matched[r] = {"run_recall": mn.pct(mn.avg(own)), "mv2_recall": mn.pct(mn.avg(mine)),
                      "mv2_ceiling": mn.pct(mn.avg(top)),
                      "run_words": br.r4(mn.avg([words(systems[r][q]) for q in qs])),
                      "mv2_words": br.r4(mn.avg([words(cut(me[q], words(systems[r][q]))) for q in qs])),
                      "questions_mv2_higher": sum(1 for a, b in zip(mine, own) if a > b),
                      "questions_equal": sum(1 for a, b in zip(mine, own) if a == b),
                      "questions_mv2_lower": sum(1 for a, b in zip(mine, own) if a < b)}
    res = {"questions": len(qs), "runs": len(runs),
           "mv2_answered": sum(1 for q in qs if me[q]),
           "matched_length": {
               "runs_beaten": sum(1 for v in matched.values() if v["mv2_recall"] > v["run_recall"]),
               "runs_tied": sum(1 for v in matched.values() if v["mv2_recall"] == v["run_recall"]),
               "runs_beaten_by_ceiling": sum(1 for v in matched.values() if v["mv2_ceiling"] > v["run_recall"]),
               "mean_gap": br.r4(mn.avg([v["mv2_recall"] - v["run_recall"] for v in matched.values()])),
               "mean_ceiling_gap": br.r4(mn.avg([v["mv2_ceiling"] - v["run_recall"] for v in matched.values()])),
               "mean_word_shortfall": br.r4(mn.avg([v["run_words"] - v["mv2_words"] for v in matched.values()])),
               "per_run": matched},
           "fixed_budget": {}}
    for b in BUDGETS:
        k = key(b)
        vals = [per[r]["recall"][k] for r in runs]
        tops = [per[r]["ceiling"][k] for r in runs]
        res["fixed_budget"][k] = {"mv2_recall": per[NAME]["recall"][k],
                                  "mv2_rank": 1 + sum(1 for v in vals if v > per[NAME]["recall"][k]),
                                  "of": len(runs) + 1,
                                  "runs_median": br.r4(statistics.median(vals)) if vals else None,
                                  "runs_max": max(vals, default=None),
                                  "mv2_ceiling": per[NAME]["ceiling"][k],
                                  "runs_ceiling_median": br.r4(statistics.median(tops)) if tops else None,
                                  "runs_ceiling_max": max(tops, default=None)}
    res["mv2_shuffled_recall"] = per[NAME]["shuffled_recall"]
    return res, per


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)  # BioGen 2024 topics.json and assessments.json
    ap.add_argument("--medaesqa-dir", required=True)
    ap.add_argument("--official", required=True)
    ap.add_argument("--answers", required=True)  # MV2's t2dev-v1 answers.jsonl
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    res, per, t0 = {"version": VERSION, "medaesqa_nugget_version": mn.VERSION,
                    "biogen_reuse_version": br.VERSION, "problem": None}, {}, time.time()
    try:
        topics_path = os.path.join(a.data_dir, "topics.json")
        assess_path = os.path.join(a.data_dir, "assessments.json")
        med_path = os.path.join(a.medaesqa_dir, "medaesqa_v1.json")
        dl = [br.download(br.TOPICS_URL, topics_path), br.download(br.ASSESS_URL, assess_path),
              br.download(mn.MEDAESQA_URL, med_path)]
        res["download"] = dl
        for d, want in zip(dl, (br.TOPICS_SHA, br.ASSESS_SHA, mn.MEDAESQA_SHA)):
            if d["sha256"] != want:
                raise ValueError("%s: sha256 %s, pinned %s" % (d["url"], d["sha256"], want))
        with open(topics_path, encoding="utf-8-sig") as f:
            tq = mn.topic_questions(json.load(f))
        with open(assess_path, encoding="utf-8-sig") as f:
            data = br.load_runs(json.load(f))
        with open(med_path, encoding="utf-8-sig") as f:
            expert, _, fields = mn.load_expert(json.load(f))
        with open(a.official, encoding="utf-8") as f:
            official = json.load(f)["runs"]
        mv2 = load_mv2(a.answers)
        qmap, how = mn.match_questions(expert, data, tq)
        tmap, thow = map_topics(qmap, mv2, expert, tq)
        res.update({"nugget_fields": fields, "question_match": how, "mv2_answers": len(mv2),
                    "mv2_sentences": sum(len(v) for v in mv2.values()), "mv2_match": thow})
        base, _ = mn.analyse(expert, qmap, data, official)
        tau = base["run_tau"]
        res["yardstick"] = {**{k: base.get(k) for k in YARDSTICK_KEYS},
                            "recall_vs_completeness_r": tau[str(BAR)]["recall_vs_completeness_r"],
                            "length_vs_completeness_r": tau["length_vs_completeness_r"],
                            "words_vs_completeness_r": tau["words_vs_completeness_r"],
                            "partial_recall_vs_completeness_r_given_length":
                                tau["partial_recall_vs_completeness_r_given_length"]}
        out, per = compare(expert, qmap, data, mv2, tmap)
        res.update(out)
    except Exception as e:  # recorded, never hidden
        res["problem"] = "%s: %s" % (type(e).__name__, e)
    res["seconds"] = round(time.time() - t0, 1)
    br.dump(os.path.join(a.out_dir, "mv2_nugget.json"), res)
    br.dump(os.path.join(a.out_dir, "mv2_systems.json"), per)
    print(json.dumps({k: v for k, v in res.items() if k != "matched_length"}, indent=1)[:6000])
    return 1 if res["problem"] else 0


if __name__ == "__main__":
    sys.exit(main())
