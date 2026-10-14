# Trajectory demo

A runnable demo of Sai's multi-turn trajectory eval. It reads a scenario with a fact ledger and per-turn annotations for two agents, and reports how far each agent's behavior falls behind the context the user has given. See [docs/trajectory.md](../docs/trajectory.md) for the method.

Watch the full prototype in the [demo video](https://youtu.be/ZK8YWPX-pMc).

## Run

```bash
python trajectory.py
python trajectory.py --svg ../assets/trajectory_example.svg
```

## What it shows

For every turn, the available context (weight of facts revealed so far), the integrated context (weight of facts the response reflects), the gap, and which facts were missed, contradicted, or replaced by an assumption. Then the summary measures. Mean and max gap, gap events, recovery time, self-recoveries, user corrections spent, late residual gap, and unstated assumptions.

![Synthetic example of two trajectories](../assets/trajectory_example.svg)

In the bundled example, Agent A misses one fact and picks it up when the user adds new information. Agent B contradicts what the user said, catches up only after being corrected, and ends with context it never used.

## Data

`example_scenario.json` is synthetic. The scenario, weights, agent names, and annotations are invented to show the format. The real tool collects responses through model APIs and stores annotations per annotator and round, and none of that data is included.
