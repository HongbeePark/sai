"""Multi-turn trajectory demo for Sai.

Reads a scenario with a fact ledger and per-turn annotations, then prints how
far each agent's behavior falls behind the context the user has actually given.

Standard library only. The bundled data is synthetic.

    python trajectory.py                      # print the report
    python trajectory.py --svg out.svg        # also write a chart
"""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).parent
GAP_THRESHOLD = 5  # a gap above this many weight points counts as an open gap


def available_facts(scenario, turn_no):
    return [f for f in scenario["facts"] if f["revealed"] <= turn_no]


def trace(scenario, model):
    """Per-turn available context, integrated context, and gap."""
    rows = []
    for t in scenario["turns"]:
        n = t["turn"]
        ann = model["turns"].get(str(n), {})
        states = ann.get("facts", {})
        avail = available_facts(scenario, n)
        ceiling = sum(f["weight"] for f in avail)
        integrated = sum(
            f["weight"] for f in avail if states.get(f["id"]) in ("used", "na")
        )
        contradicted = [f["id"] for f in avail if states.get(f["id"]) == "contradicted"]
        missed = [f["id"] for f in avail if states.get(f["id"]) == "missed"]
        rows.append(
            {
                "turn": n,
                "kind": t["kind"],
                "available": ceiling,
                "integrated": integrated,
                "gap": ceiling - integrated,
                "missed": missed,
                "contradicted": contradicted,
                "assumptions": ann.get("assumptions", []),
            }
        )
    return rows


def metrics(rows):
    """Summary statistics. Meta turns (e.g. 'summarize') are excluded."""
    s = [r for r in rows if r["kind"] != "meta"]
    gaps = [r["gap"] for r in s]
    events = self_recoveries = corrections = 0
    open_since = None
    recovery_times = []
    for i, r in enumerate(s):
        prev = gaps[i - 1] if i else 0
        if r["kind"] in ("restate", "negate"):
            corrections += 1  # the user had to repeat or correct: a cost, not a recovery
        if r["gap"] > GAP_THRESHOLD and prev <= GAP_THRESHOLD:
            events += 1
            open_since = i
        if open_since is not None and r["gap"] <= GAP_THRESHOLD:
            recovery_times.append(i - open_since)
            if r["kind"] == "reveal":
                self_recoveries += 1
            open_since = None
    late = gaps[-max(1, len(gaps) // 3):]
    return {
        "mean_gap": round(sum(gaps) / len(gaps), 1),
        "max_gap": max(gaps),
        "gap_events": events,
        "self_recoveries": self_recoveries,
        "user_corrections_spent": corrections,
        "mean_recovery_turns": round(sum(recovery_times) / len(recovery_times), 1)
        if recovery_times
        else None,
        "still_open_at_end": open_since is not None,
        "late_residual_gap": round(sum(late) / len(late), 1),
        "unstated_assumptions": sum(len(r["assumptions"]) for r in s),
    }


def print_report(scenario, models):
    print(f"Scenario: {scenario['title']}\n")
    for key, model in models.items():
        rows = trace(scenario, model)
        print(model["label"])
        print(f"  {'turn':>4} {'kind':<8} {'avail':>5} {'integ':>5} {'gap':>4}  notes")
        for r in rows:
            notes = []
            if r["missed"]:
                notes.append("missed " + ",".join(r["missed"]))
            if r["contradicted"]:
                notes.append("contradicted " + ",".join(r["contradicted"]))
            if r["assumptions"]:
                notes.append("assumed: " + "; ".join(r["assumptions"]))
            print(
                f"  {r['turn']:>4} {r['kind']:<8} {r['available']:>5} "
                f"{r['integrated']:>5} {r['gap']:>4}  {' | '.join(notes)}"
            )
        for k, v in metrics(rows).items():
            print(f"  {k:<24}{v}")
        print()


def write_svg(scenario, models, path):
    """Small-multiple chart: available context vs. integrated context per model."""
    w, h, pad = 360, 240, 40
    keys = list(models)
    total_w = w * len(keys)
    turns = [t["turn"] for t in scenario["turns"]]
    ymax = sum(f["weight"] for f in scenario["facts"])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{h + 30}" '
        f'viewBox="0 0 {total_w} {h + 30}" font-family="-apple-system, Helvetica, Arial, sans-serif" font-size="11">',
        f'<rect width="{total_w}" height="{h + 30}" fill="#ffffff"/>',
    ]

    def x(i, ox):
        return ox + pad + (w - 2 * pad) * (i - 1) / (len(turns) - 1)

    def y(v):
        return pad + (h - 2 * pad) * (1 - v / ymax)

    for idx, key in enumerate(keys):
        ox = idx * w
        rows = trace(scenario, models[key])
        parts.append(f'<text x="{ox + pad}" y="22" font-size="13" fill="#111">{models[key]["label"]}</text>')
        parts.append(
            f'<line x1="{ox + pad}" y1="{h - pad}" x2="{ox + w - pad}" y2="{h - pad}" stroke="#bbb"/>'
        )
        avail = " ".join(f"{x(r['turn'], ox):.1f},{y(r['available']):.1f}" for r in rows)
        integ = " ".join(f"{x(r['turn'], ox):.1f},{y(r['integrated']):.1f}" for r in rows)
        gap_poly = avail + " " + " ".join(
            f"{x(r['turn'], ox):.1f},{y(r['integrated']):.1f}" for r in reversed(rows)
        )
        parts.append(f'<polygon points="{gap_poly}" fill="#e4572e" fill-opacity="0.15"/>')
        parts.append(f'<polyline points="{avail}" fill="none" stroke="#888" stroke-dasharray="4 3" stroke-width="2"/>')
        parts.append(f'<polyline points="{integ}" fill="none" stroke="#1f6feb" stroke-width="2.5"/>')
        for r in rows:
            cx, cy = x(r["turn"], ox), y(r["integrated"])
            fill = "#e4572e" if r["contradicted"] or r["assumptions"] else "#1f6feb"
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{fill}"/>')
            label = r["turn"] if r["kind"] == "reveal" else f'{r["turn"]}{r["kind"][0]}'
            parts.append(f'<text x="{cx:.1f}" y="{h - pad + 15}" text-anchor="middle" fill="#555">{label}</text>')
    parts.append(
        f'<text x="{pad}" y="{h + 6}" fill="#555">dashed = context the user has given · '
        f'blue = context reflected in the response · shaded = gap</text>'
    )
    parts.append(
        f'<text x="{pad}" y="{h + 22}" fill="#555">red dot = contradiction or unstated assumption · '
        f'r / n / m = restate / negate / meta turn</text>'
    )
    parts.append("</svg>")
    Path(path).write_text("\n".join(parts), encoding="utf-8")
    print(f"Chart written to {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=HERE / "example_scenario.json")
    ap.add_argument("--svg", help="write a trajectory chart to this path")
    args = ap.parse_args()
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    print_report(data["scenario"], data["models"])
    if args.svg:
        write_svg(data["scenario"], data["models"], args.svg)


if __name__ == "__main__":
    main()
