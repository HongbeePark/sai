# Framework

This page describes what Sai measures at a conceptual level. Operational scoring anchors, judge prompts, and study materials are not included.

## The unit of analysis

Sai does not grade a single answer as good or bad. It asks how a response relates to the person who prompted it.

- What did the person actually say?
- What did the agent take from that?
- What did the agent add that the person never said?
- What did the agent leave out that the person clearly cared about?

## Fact and assumption

The central distinction in Sai is between context the user gave and context the agent supplied.

![The fact ledger](../assets/fact_ledger.svg)

**Fact ledger.** Each piece of decision-relevant context the user provides is listed as a fact, with the turn it appears in and a weight for how much it should matter to the decision. The ledger is written before any agent is run, so the standard is fixed in advance and never drawn after seeing the outputs.

**Fact states.** For each response, annotators record whether every available fact was

- used, meaning the response reflects it,
- missed, meaning the response ignores it,
- contradicted, meaning the response assumes the opposite, or
- not applicable at that point in the conversation.

**Span codes.** Annotators also highlight the text of the response.

- Grounded text follows from what the user said.
- Unsupported text treats something the user never said as a premise.
- Contradiction text rests on the opposite of what the user said.
- Filler carries no decision-relevant content.

Together these give two views of the same response. The fact states show what the agent took in. The spans show what the agent built on.

![What each response rests on](../assets/behavior_lab_shares.svg)

**Elicitation.** Annotators also log what the response asked the user, and whether that question anticipated something the user later revealed, asked again for something already given, or asked about something outside the ledger.

## Behavioral axes

Alongside the ledger, responses are scored on a small set of behavioral axes. Each describes a tendency, not a verdict. A high score is not automatically bad. What matters is whether the level fits the amount of context available.

| Axis | What it describes |
| --- | --- |
| Certainty | How settled the agent presents its reading of the situation |
| Directiveness | How strongly the agent pushes the user toward one action |
| Interpretation lock-in | How firmly the agent commits to one reading of the situation |
| Possibility exploration | How many genuinely different paths or readings the agent considers |
| Context seeking | Whether the agent asks for the missing information that would change its answer |
| Answer priority | Whether the agent answers first or seeks context first |
| Assumption adoption | How readily the agent fills gaps and then reasons from what it filled in |
| Consequence escalation | How far the agent projects serious outcomes from limited clues |

The working hypothesis is that a well-adapting agent calibrates these tendencies to what it actually knows. Early in a conversation, with little context, it should hold its reading loosely and ask. As context accumulates, it can commit more. A failure is a mismatch between the level of commitment and the evidence behind it.

## Integration stays separate from the axes

How much of the user's context a response reflects (integration) is annotated directly from the fact ledger. It is never computed from the axis scores. Keeping the two separate means the axes can be used to explain integration failures without the explanation becoming circular.

## People first, judges second

Every annotation is stored with who made it and in which round, so the same responses can be coded independently. People code first. Two LLM judges then score the same responses blind to each other. When the judges agree, the value stands. When they differ by one point, the mean is used. A wider split goes to a person. A judge is used on new data only after its agreement with human coders reaches a set target.

![People first, judges second](../assets/calibration.svg)
