"""Exact fixed-point emulator for invsqrt pipelines (Google Quantum AI / Kaggle VQCC, Benchmark I).

MV2 of Munim, Inc. (made with AI agents working in his name). Apache-2.0.

The task (arXiv:2610.23832, Benchmark I and Appendix B): for every x in [1, 3,133,452] in a
22-qubit register, apply a phase of 1/sqrt(x) turns to within 2^-24/sqrt(x) turns. A kickmix
circuit computes a fixed-point value y, applies one Z_POW per bit of y, and uncomputes. This
module reproduces that arithmetic with exact integers in numpy over every input, so a design's
worst error is known before any circuit is written.

Toffoli and qubit numbers here are a MODEL (the formulas in mac_cost and poly_cost), not a count
of a built circuit. The rotation price is the paper's: 0.56 log2(1/eps) + 5.3 T per fine Z_POW,
eps = pi * min_x(tol - err) / n_rot.

Two pipelines:
- ref: the paper's reference (normalize, 4-case cubic from QROM at 17 fractional bits, one
  Newton step with truncated multipliers, shift back, phase). Used to check this emulator.
- poly: normalize, a piecewise polynomial of degree d from one QROM (2^a_lo segments on [1,2),
  2^a_hi on [2,4)), signed Horner with truncated multipliers, no Newton step, shift back, phase.
  A greedy search trims each stage's fractional bits while every input still passes.

  python isqrt_emul.py --out /out/emul.json
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

VERSION = "0.1.0"
N_P = 10
NBITS = 2 * N_P + 2            # 22-qubit input register
FRAC = NBITS - 2               # x_norm has 20 fractional bits, value in [1, 4)
X_MAX = 3 * (2 ** N_P - 2) ** 2  # 3,133,452
TOL_LOG2 = -24
PASS_FRACTION = 15 / 16        # the search keeps worst relative error <= 15/16 of the tolerance
REF = {"qubits": 260, "toffoli": 7735, "rotations": 37, "C": 7987.59, "cost": 2076774.23,
       "horner": 1071, "mantissa": 1043, "final": 867, "worst_log2": -25.07, "worst_x": 2588411}

# arXiv:2610.23832 Eqs. 15-16 (attributed there to its Ref. [29]).
A = (0.99994132489119882162, 0.49609891915903542303, 0.33261112772430493331, 0.14876762006038398086)
B = (0.81648515205385221995, 0.27136515484240234115, 0.12756148214815175348, 0.044753028579153842218)

# (degree, a_hi) pairs screened by default; a_lo runs over a_hi and a_hi + 1.
DEFAULT_GRID = ((1, 9), (1, 10), (1, 11), (2, 5), (2, 6), (2, 7),
                (3, 3), (3, 4), (3, 5), (4, 2), (4, 3), (4, 4))


def all_x(x_max=X_MAX):
    return np.arange(1, x_max + 1, dtype=np.int64)


def normalize(x):
    """Shift x left by pairs until its top pair is not 00. Returns (xn, s); xn in [2^20, 2^22)."""
    xn = np.array(x, dtype=np.int64, copy=True)
    s = np.zeros(xn.shape, dtype=np.int64)
    for _ in range(N_P):
        m = xn < (1 << FRAC)
        xn[m] <<= 2
        s[m] += 1
    return xn, s


def tmul(a, fa, b, fb, nb, fout):
    """Truncated product T(a*b) at fout fractional bits. Rows run over the nb low bits of the
    unsigned b (fb fractional bits); each row drops its partial-product bits below 2^-fout, which
    is an arithmetic right shift (floor) of the signed multiplicand a (fa fractional bits)."""
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    acc = np.zeros(np.broadcast(a, b).shape, dtype=np.int64)
    for i in range(nb):
        e = i - fb - fa + fout
        row = (a << e) if e >= 0 else (a >> min(-e, 62))
        acc += row * ((b >> i) & 1)
    return acc


def width(v):
    """Register width for the integer values v (two's complement if any is negative)."""
    v = np.asarray(v, dtype=np.int64)
    mx, mn = int(np.max(v)), int(np.min(v))
    if mn >= 0:
        return max(1, mx.bit_length())
    return max(mx.bit_length(), (-mn - 1).bit_length()) + 1


def rel_err(y, F, x):
    """|y 2^-F sqrt(x) - 1| for the phase y (F fractional bits of a turn)."""
    return np.abs(y.astype(np.float64) * 2.0 ** -F * np.sqrt(np.asarray(x, dtype=np.float64)) - 1.0)


def stats(rel, x):
    x = np.asarray(x)
    i = int(np.argmax(rel))
    worst = float(rel[i])
    tol = 2.0 ** TOL_LOG2
    margin = float(np.min((tol - rel) / np.sqrt(x.astype(np.float64))))
    return {"worst_rel": worst, "worst_log2": round(math.log2(worst), 3) if worst > 0 else None,
            "worst_x": int(x[i]), "fails": int(np.count_nonzero(rel > tol)),
            "margin_turns": margin, "margin_log2": round(math.log2(margin), 3) if margin > 0 else None}


def rotation_t(margin_turns, n_rot):
    """T gates per fine Z_POW (paper's mixed-fallback price), or None if there is no margin."""
    if margin_turns <= 0 or n_rot <= 0:
        return None
    eps = math.pi * margin_turns / n_rot
    return 0.56 * math.log2(1.0 / eps) + 5.3


def mac_cost(w_mult, f_mult, f_out, w_acc, fb, nb):
    """Model Toffolis of acc += T(mult * b), rows over nb bits of b (fb fractional bits): per row
    with any kept partial product, one AND per kept multiplicand bit plus a w_acc-bit adder.
    Returns (ands, adder_toffolis, widest row)."""
    ands = adds = widest = 0
    for i in range(nb):
        m = max(0, w_mult - max(0, f_mult + fb - i - f_out))
        if m:
            ands += m
            adds += w_acc
            widest = max(widest, m)
    return ands, adds, widest


# ---------------------------------------------------------------- reference pipeline

def ref_tables(fc=17):
    """Integer coefficient tables c[k][case], case = 2 * upper + use_b, at fc fractional bits."""
    out = []
    for k in range(4):
        r = []
        for upper in (0, 1):
            for coef in (A, B):
                v = coef[k] / (math.sqrt(2.0) * 2 ** k if upper else 1.0)
                r.append(int(round(v * 2 ** fc)))
        out.append(np.array(r, dtype=np.int64))
    return out


def ref_pipeline(x, fc=17, wdx=14, fsq=28, fz=28, fp=29):
    """The reference arithmetic. Returns (phase integer, F, intermediates)."""
    xn, s = normalize(x)
    upper = (xn >> (FRAC + 1)) & 1
    use_b = np.where(upper == 1, (xn >> FRAC) & 1, (xn >> (FRAC - 1)) & 1)
    frac = xn & ((1 << FRAC) - 1)
    dx = np.where(upper == 1, frac, frac & ~(1 << (FRAC - 1)))
    d = dx >> (FRAC - wdx)
    case = 2 * upper + use_b
    c = [t[case] for t in ref_tables(fc)]
    t3 = c[3]
    t2 = c[2] - tmul(t3, fc, d, wdx, wdx, fc)
    t1 = c[1] - tmul(t2, fc, d, wdx, wdx, fc)
    y0 = c[0] - tmul(t1, fc, d, wdx, wdx, fc)
    sq = tmul(y0, fc, y0, fc, fc + 1, fsq)
    z = tmul(sq, fsq, xn, FRAC, NBITS, fz)
    w = (3 << fz) - z
    p = tmul(w, fz, y0, fc, fc + 1, fp)          # ~ 2 / sqrt(x_norm)
    F = fp + 1 + N_P
    return p << s, F, {"t3": t3, "t2": t2, "t1": t1, "y0": y0, "sq": sq, "z": z, "w": w, "p": p}


def ref_report(x):
    y, F, mid = ref_pipeline(x)
    st = stats(rel_err(y, F, x), x)
    n_rot = F - 3
    per = rotation_t(st["margin_turns"], n_rot)
    wd = {k: width(v) for k, v in mid.items()}
    h = [mac_cost(wd["t3"], 17, 17, wd["t2"], 14, 14), mac_cost(wd["t2"], 17, 17, wd["t1"], 14, 14),
         mac_cost(wd["t1"], 17, 17, wd["y0"], 14, 14)]
    mant = mac_cost(wd["sq"], 28, 28, wd["z"], FRAC, NBITS)
    fin = mac_cost(wd["w"], 28, 29, wd["p"], 17, 18)
    return {"F": F, "n_rot": n_rot, "rotation_t_each": round(per, 3) if per else None,
            "widths": wd, "stats": st,
            "model": {"horner": sum(a + b for a, b, _ in h), "mantissa": mant[0] + mant[1],
                      "final": fin[0] + fin[1]},
            "paper": {k: REF[k] for k in ("horner", "mantissa", "final", "worst_log2", "worst_x")}}


# ---------------------------------------------------------------- piecewise polynomial pipeline

class Layout:
    """Segments: 2^a_lo on [1,2), 2^a_hi on [2,4). t = the low D = 21 - a_hi bits of x_norm, so
    every segment's polynomial is in t = X - base, base = X with those bits cleared."""

    def __init__(self, a_lo, a_hi):
        if a_lo < a_hi - 1:
            raise ValueError("a_lo must be >= a_hi - 1")
        self.a_lo, self.a_hi = a_lo, a_hi
        self.D = FRAC + 1 - a_hi
        self.L = 2 ** a_lo + 2 ** a_hi

    def seg_t(self, xn):
        lower = xn < (1 << (FRAC + 1))
        seg = np.where(lower, (xn - (1 << FRAC)) >> (FRAC - self.a_lo),
                       2 ** self.a_lo + ((xn - (1 << (FRAC + 1))) >> self.D))
        return seg, xn & ((1 << self.D) - 1)

    def interval(self, j):
        """(lo, hi, base) of segment j in X units."""
        if j < 2 ** self.a_lo:
            h = 2.0 ** -self.a_lo
            lo = 1.0 + j * h
        else:
            h = 2.0 ** (1 - self.a_hi)
            lo = 2.0 + (j - 2 ** self.a_lo) * h
        cell = 2.0 ** (self.D - FRAC)
        return lo, lo + h, math.floor(lo / cell) * cell


def fit(layout, degree):
    """Float coefficients c[k][j] of a near-minimax (relative) fit of X^-1/2 in t = X - base."""
    n = 4 * degree + 8
    cs = np.cos(np.pi * (np.arange(n) + 0.5) / n)
    out = np.zeros((degree + 1, layout.L))
    for j in range(layout.L):
        lo, hi, base = layout.interval(j)
        X = 0.5 * (lo + hi) + 0.5 * (hi - lo) * cs
        f = X ** -0.5
        out[:, j] = np.polyfit(X - base, f, degree, w=1.0 / f)[::-1]
    return out


def poly_values(cint, f, seg, t, D):
    """Signed Horner: acc_d = c_d; acc_k = c_k + T(acc_{k+1} * t). Returns [acc_0, ..., acc_d]."""
    d = len(cint) - 1
    accs = [None] * (d + 1)
    accs[d] = cint[d][seg]
    for k in range(d - 1, -1, -1):
        accs[k] = cint[k][seg] + tmul(accs[k + 1], f[k + 1], t, FRAC, D, f[k])
    return accs


class Design:
    """One (degree, a_lo, a_hi) layout evaluated over a fixed set of inputs x."""

    def __init__(self, degree, a_lo, a_hi, x):
        self.degree, self.lay = degree, Layout(a_lo, a_hi)
        self.x = np.asarray(x, dtype=np.int64)
        self.xn, self.s = normalize(self.x)
        self.seg, self.t = self.lay.seg_t(self.xn)
        self.sqrt_X = np.sqrt(self.xn.astype(np.float64) / 2 ** FRAC)
        self.coef = fit(self.lay, degree)
        order = np.argsort(self.seg, kind="stable")
        self.order = order
        self.uniq, self.starts = np.unique(self.seg[order], return_index=True)

    def evaluate(self, f):
        """Quantize at fractional bits f[k], run Horner, re-centre c0 per segment, return
        (stats, c0-centred integer tables, accumulator values)."""
        cint = [np.rint(self.coef[k] * 2.0 ** f[k]).astype(np.int64) for k in range(self.degree + 1)]
        accs = poly_values(cint, f, self.seg, self.t, self.lay.D)
        ae = accs[0].astype(np.float64) - 2.0 ** f[0] / self.sqrt_X
        srt = ae[self.order]
        mx = np.maximum.reduceat(srt, self.starts)
        mn = np.minimum.reduceat(srt, self.starts)
        delta = np.zeros(self.lay.L, dtype=np.int64)
        delta[self.uniq] = -np.rint(0.5 * (mx + mn)).astype(np.int64)
        cint[0] = cint[0] + delta
        accs[0] = accs[0] + delta[self.seg]
        F = f[0] + N_P
        st = stats(rel_err(accs[0] << self.s, F, self.x), self.x)
        return st, cint, accs

    def passes(self, st):
        return st["fails"] == 0 and st["worst_rel"] <= PASS_FRACTION * 2.0 ** TOL_LOG2

    def search(self, f_start=32, f_min=6):
        """Greedy: from f_start everywhere, binary-search each stage's smallest passing f_k,
        highest degree first. Returns the result dict (feasible False if f_start fails)."""
        f = [f_start] * (self.degree + 1)
        st, _, _ = self.evaluate(f)
        evals = 1
        if not self.passes(st):
            return {"feasible": False, "start_stats": st, "evals": evals}
        for k in range(self.degree, -1, -1):
            lo, hi = f_min, f[k]
            while lo < hi:
                mid = (lo + hi) // 2
                trial = list(f)
                trial[k] = mid
                st_m, _, _ = self.evaluate(trial)
                evals += 1
                if self.passes(st_m):
                    hi = mid
                else:
                    lo = mid + 1
            f[k] = hi
        st, cint, accs = self.evaluate(f)
        evals += 1
        if not self.passes(st):          # greedy steps are not monotone; report and stop
            return {"feasible": False, "f": f, "final_stats": st, "evals": evals}
        cost = poly_cost(self.degree, self.lay, f, cint, accs, st)
        return {"feasible": True, "f": f, "stats": st, "cost": cost, "evals": evals}


def qrom_cost(L):
    fwd = L - 1
    back = min(math.ceil(L / k) + k for k in (2 ** i for i in range(0, max(1, L.bit_length()))))
    return fwd, back


def poly_cost(degree, lay, f, cint, accs, st):
    """Cost MODEL of the poly pipeline (forward + reverse). See the module docstring."""
    w = [max(width(cint[k]), width(accs[k])) for k in range(degree + 1)]
    ands = adds = widest = 0
    for k in range(degree - 1, -1, -1):
        a, b, m = mac_cost(w[k + 1], f[k + 1], f[k], w[k], FRAC, lay.D)
        ands, adds, widest = ands + a, adds + b, max(widest, m)
    horner = ands + adds
    norm = N_P * (N_P + 2) + N_P * (N_P + 1)
    q_fwd, q_back = qrom_cost(lay.L)
    denorm = 2 * N_P * w[0]
    tof = 2 * horner + norm + q_fwd + q_back + denorm
    F = f[0] + N_P
    n_rot = F - 3
    per = rotation_t(st["margin_turns"], n_rot)
    C = tof + (n_rot * per + 1) / 4.0
    Q = NBITS + N_P + sum(w) + N_P + widest + max(w) + math.ceil(math.log2(lay.L))
    return {"widths": w, "L": lay.L, "D": lay.D, "toffoli": {"horner_each_way": horner,
            "horner_ands": ands, "horner_adders": adds, "normalize": norm, "qrom": q_fwd,
            "qrom_uncompute": q_back, "denormalize": denorm, "total": tof},
            "F": F, "n_rot": n_rot, "rotation_t_each": round(per, 3), "C": round(C, 2), "Q": Q,
            "QxC": round(Q * C, 1), "ratio_vs_reference": round(REF["cost"] / (Q * C), 3)}


def screen(x, grid=DEFAULT_GRID, log=print):
    rows = []
    for degree, a_hi in grid:
        for a_lo in (a_hi, a_hi + 1):
            t0 = time.time()
            r = Design(degree, a_lo, a_hi, x).search()
            r.update({"degree": degree, "a_lo": a_lo, "a_hi": a_hi, "seconds": round(time.time() - t0, 1)})
            rows.append(r)
            c = r.get("cost", {})
            log(json.dumps({"degree": degree, "a_lo": a_lo, "a_hi": a_hi, "feasible": r["feasible"],
                            "f": r.get("f"), "QxC": c.get("QxC"), "ratio": c.get("ratio_vs_reference"),
                            "seconds": r["seconds"]}))
    ok = [r for r in rows if r["feasible"]]
    best = min(ok, key=lambda r: r["cost"]["QxC"]) if ok else None
    return rows, best


def parse_grid(text):
    out = []
    for part in text.split(";"):
        d, a = part.split(",")
        out.append((int(d), int(a)))
    return tuple(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--x-max", type=int, default=X_MAX)
    ap.add_argument("--grid", default=None, help="'degree,a_hi;degree,a_hi' (default: DEFAULT_GRID)")
    a = ap.parse_args(argv)
    t0 = time.time()
    x = all_x(a.x_max)
    rep = {"version": VERSION, "numpy": np.__version__, "x_max": a.x_max, "n_inputs": int(x.size),
           "pass_fraction": PASS_FRACTION}
    rep["reference"] = ref_report(x)
    print(json.dumps({"reference": rep["reference"]["stats"], "model": rep["reference"]["model"],
                      "rotation_t_each": rep["reference"]["rotation_t_each"]}))
    grid = parse_grid(a.grid) if a.grid else DEFAULT_GRID
    rows, best = screen(x, grid)
    rep["designs"] = rows
    rep["best"] = None if best is None else {k: best[k] for k in ("degree", "a_lo", "a_hi", "f", "stats", "cost")}
    rep["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps({"best": rep["best"], "seconds": rep["seconds"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
