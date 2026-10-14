"""Behavior Lab demo for Sai.

Shows two things the Behavior Lab does with annotated responses.

1. Fact vs. assumption share. Annotators highlight each response as grounded
   (follows from what the user said), unsupported (treats something the user
   never said as a premise), contradiction (assumes the opposite of what the
   user said), or filler. The demo reports how much of each response rests on
   the user's words and how much rests on the model's own assumptions.

2. Agreement before automation. Two human annotators and two LLM judges score
   the same responses on behavioral axes. The demo reports human-human and
   human-judge agreement and builds the adjudication queue that a person
   resolves before any judge is trusted on its own.

Standard library only. The bundled data is synthetic.

    python agreement.py
    python agreement.py --svg shares.svg      # also chart the fact vs. assumption shares
"""

import argparse
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).parent
HUMANS = ("annotator-1", "annotator-2")
JUDGES = ("judge-a", "judge-b")


def span_shares(resp):
    total = resp["length"]
    by = {}
    for s in resp["spans"]:
        by[s["code"]] = by.get(s["code"], 0) + s["chars"]
    marked = sum(by.values())
    grounded = by.get("grounded", 0)
    assumed = by.get("unsupported", 0) + by.get("contradiction", 0)
    return {
        "grounded_pct": round(100 * grounded / total),
        "assumed_pct": round(100 * assumed / total),
        "coverage_pct": round(100 * marked / total),
    }


def judge_consensus(a, b):
    """Agreement keeps the value, a one-point split takes the mean,
    a wider split goes to a person."""
    if a == b:
        return a, False
    if abs(a - b) == 1:
        return (a + b) / 2, False
    return None, True


def pair_stats(responses, axes, x, y):
    diffs = [
        abs(r["scores"][x][ax] - r["scores"][y][ax]) for r in responses for ax in axes
    ]
    n = len(diffs)
    return {
        "exact": round(100 * sum(d == 0 for d in diffs) / n),
        "within_1": round(100 * sum(d <= 1 for d in diffs) / n),
        "mae": round(sum(diffs) / n, 2),
    }


def write_svg(responses, path):
    """Stacked bar per response: grounded, assumed (unsupported + contradiction), filler, unmarked."""
    font = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
    segs = [("grounded", "#1f6feb"), ("assumed", "#e4572e"), ("filler", "#8c959f"), ("unmarked", "#d0d7de")]
    w, row, left, top = 760, 44, 210, 92
    h = top + row * len(responses) + 60
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{font}">',
           f'<rect width="{w}" height="{h}" rx="10" fill="#ffffff"/>',
           '<text x="40" y="44" font-size="20" font-weight="600" fill="#1b1f24">What each response rests on</text>',
           '<text x="40" y="68" font-size="14" fill="#57606a">Share of response text, synthetic example</text>']
    bw = w - left - 60
    for i, r in enumerate(responses):
        by = {}
        for s in r["spans"]:
            key = "assumed" if s["code"] in ("unsupported", "contradiction") else s["code"]
            by[key] = by.get(key, 0) + s["chars"]
        by["unmarked"] = r["length"] - sum(by.values())
        y = top + i * row
        out.append(f'<text x="40" y="{y + 20}" font-size="13" fill="#1b1f24">{r["id"]} · {r["model"]}</text>')
        out.append(f'<text x="40" y="{y + 36}" font-size="11" fill="#57606a">{r["condition"]}</text>')
        x = left
        for key, color in segs:
            seg = bw * by.get(key, 0) / r["length"]
            if seg > 0:
                out.append(f'<rect x="{x:.1f}" y="{y + 6}" width="{max(seg - 2, 1):.1f}" height="24" rx="4" fill="{color}"/>')
                if key in ("grounded", "assumed") and seg > 34:
                    pct = round(100 * by[key] / r["length"])
                    out.append(f'<text x="{x + 8:.1f}" y="{y + 23}" font-size="12" fill="#ffffff" font-weight="600">{pct}%</text>')
            x += seg
    lx, ly = 40, h - 24
    for key, color in segs:
        out.append(f'<rect x="{lx}" y="{ly - 10}" width="14" height="10" rx="3" fill="{color}"/>')
        out.append(f'<text x="{lx + 20}" y="{ly}" font-size="12" fill="#57606a">{key}</text>')
        lx += 20 + len(key) * 7 + 28
    out.append("</svg>")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    print(f"\nChart written to {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", help="write a fact vs. assumption share chart to this path")
    args = ap.parse_args()
    data = json.loads((HERE / "example_annotations.json").read_text(encoding="utf-8"))
    axes, responses = data["axes"], data["responses"]

    print("Fact vs. assumption share per response")
    print(f"  {'id':<4}{'model':<10}{'condition':<14}{'grounded':>9}{'assumed':>9}{'coverage':>10}")
    for r in responses:
        s = span_shares(r)
        print(
            f"  {r['id']:<4}{r['model']:<10}{r['condition']:<14}"
            f"{s['grounded_pct']:>8}%{s['assumed_pct']:>8}%{s['coverage_pct']:>9}%"
        )

    print("\nAgreement on behavioral axes (exact %, within-1 %, mean abs. error)")
    raters = HUMANS + JUDGES
    for x, y in combinations(raters, 2):
        st = pair_stats(responses, axes, x, y)
        print(f"  {x:<12} vs {y:<12} {st['exact']:>4}% {st['within_1']:>5}%  MAE {st['mae']}")

    print("\nJudge consensus and adjudication queue")
    queue = []
    for r in responses:
        for ax in axes:
            val, needs_human = judge_consensus(
                r["scores"][JUDGES[0]][ax], r["scores"][JUDGES[1]][ax]
            )
            human_mean = sum(r["scores"][h][ax] for h in HUMANS) / len(HUMANS)
            if needs_human:
                queue.append((r["id"], ax, r["scores"][JUDGES[0]][ax], r["scores"][JUDGES[1]][ax], human_mean))
            elif abs(val - human_mean) >= 1.5:
                queue.append((r["id"], ax, r["scores"][JUDGES[0]][ax], r["scores"][JUDGES[1]][ax], human_mean))
    if not queue:
        print("  nothing to adjudicate")
    for rid, ax, a, b, hm in queue:
        print(f"  {rid} {ax:<20} judges {a} / {b}  humans avg {hm}")
    if args.svg:
        write_svg(responses, args.svg)


if __name__ == "__main__":
    main()
