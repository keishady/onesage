# Contributing to OneSage

Thanks for your interest in OneSage.

OneSage is a Strategic Intelligence Skill. Contributions should improve strategic judgment, review, memory, or pattern quality.

## What to Contribute

### 1. Strategic Cases

Good cases help OneSage reason better.

A useful case includes:

- strategic question
- user goal
- context facts
- assumptions
- unknowns
- actual outcome if available
- what made the decision hard

Example areas:

- content creation
- startup direction
- career transition
- learning plan
- side project
- sunk cost decision

### 2. New Patterns

Pattern contributions should not come from a single anecdote.

A useful Pattern contribution includes:

- domain
- situation stage
- contradiction type
- risk type
- supporting lessons
- counter examples
- applicability boundary

Pattern rule:

```text
Current Facts > Strategic Pattern > Historical Lessons
```

### 3. New Rules

Rule contributions should improve deterministic reasoning.

Good rules are:

- explicit
- testable
- conservative
- explainable
- aligned with stop conditions

Avoid rules that:

- overfit one example
- force high commitment
- reduce risk without current evidence
- treat historical experience as fact

### 4. Code Contributions

Before changing code:

- keep the strategic boundary intact
- do not add autonomous execution
- do not add external API calls unless the roadmap explicitly allows it
- do not modify legacy execution paths unless the issue explicitly requires it
- add tests or manual verification notes

## Development Setup

```bash
cd onesage-v0.4
python -m pip install -e .
```

Run a local strategic judgment:

```bash
python -m onesage.cli strategize "Should I continue this project?"
```

Run a saved judgment and review:

```bash
python -m onesage.cli strategize "Should I continue this project?" --save
python -m onesage.cli review 1 "The test failed, but revealed one useful segment."
```

## Contribution Style

Please keep contributions:

- small
- reviewable
- documented
- deterministic where possible
- respectful of existing architecture

## What OneSage Should Not Become

OneSage should not become:

- Autonomous Agent
- Tool Executor
- Workflow Engine
- Browser automation tool
- Shell automation tool

OneSage's core value is strategic judgment before action.

