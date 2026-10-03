# OneSage

A strategic intelligence layer before action.

行动之前的战略军师。

OneSage is a strategic reasoning layer that helps humans and AI agents make better decisions before taking action.

## 周易决策军师 Skill（新）

`.claude/skills/zhouyi/` 是把周易 64 卦逐卦结构化后做成的 Claude Code skill：

- 每一卦 = 一类事情的**态势**：适用情境、判断要点、宜 / 忌、走向。
- 每一卦的六爻 = 事情推进的六个**阶段**，各给出爻辞与对策。
- 遇到事情直接问："我遇到 XX，该怎么办？"，skill 会判卦、定爻，并给出可执行的建议。
- `index.md` 有情境速查与八卦查卦表；`scripts/cast.py` 可三枚铜钱起卦（可选）。

下文的 Strategic Judgment CLI 是此前的 v0.1.0-alpha 实验性引擎，与上述 skill 相互独立。

## What OneSage Is

OneSage is a Decision Layer before Action.

It helps answer questions like:

- Should I continue?
- Should I invest more?
- Should I stop?
- Is this the right timing?
- What is the main contradiction?

OneSage is not:

- Autonomous Agent
- Tool Executor
- Workflow Engine

OneSage does not try to operate your computer, call external tools, browse the web, or automate workflows. Its core job is strategic judgment before action.

## Core Capabilities

### 1. Strategic Judgment Core

OneSage turns a strategic question into a structured judgment:

- Situation Analyzer
- Contradiction Analyzer
- Solvability Analysis
- Timing Analysis
- Strategic Risk
- Strategic Advice

### 2. Judgment Calibration

OneSage can review previous judgments against actual outcomes:

- Judgment Review
- Error Taxonomy
- Confidence Update
- Lesson Candidate generation

It separates judgment quality from result quality:

- Good judgment can still have a bad result.
- Bad judgment can still get lucky.

### 3. Strategic Memory

OneSage stores and retrieves strategic experience:

- Judgment Memory
- Lesson Memory
- Pattern Memory

### 4. Pattern Retrieval

OneSage can retrieve historical strategic patterns and lessons.

Historical experience only assists judgment. It does not override current facts.

## Architecture

```text
Question
|
v
Context
|
v
Situation
|
v
Contradiction
|
v
Solvability
|
v
Timing
|
v
Risk
|
v
Advice
|
v
Review
|
v
Memory
|
v
Pattern
```

## Quick Start

### Install locally

```bash
cd onesage-v0.4
python -m pip install -e .
```

OneSage currently has no third-party runtime dependencies.

### Run a strategic judgment

```bash
python -m onesage.cli strategize "Should I continue my YouTube channel?"
```

You can also use JSON output:

```bash
python -m onesage.cli strategize "Should I continue my YouTube channel?" --json
```

### Example output

```text
== OneSage Strategic Judgment ==

Conclusion: B_small_test
Plain answer: Suitable for a small test, not for directly increasing investment.

1. Input Context
- Question: Should I continue my YouTube channel?
- Domain: content

2. Situation Analysis
- Stage: competition

3. Primary Contradiction
- Primary contradiction: content differentiation vs oversupply

4. Strategic Advice
- Minimum next action: test 2-3 differentiated content directions with a small sample.
- Stop conditions: stop or rethink if no direction shows better-than-baseline signal.
```

## CLI Examples

Save a judgment:

```bash
python -m onesage.cli strategize "Should I invest six months into this startup idea?" --save
```

Review a saved judgment:

```bash
python -m onesage.cli review 1 "After 20 tests, there was no growth, but one segment showed stronger retention."
```

List lesson memory:

```bash
python -m onesage.cli memory list
```

Search strategic patterns:

```bash
python -m onesage.cli pattern search "startup demand_validation direction_risk"
```

## Project Structure

```text
onesage-v0.4/
  onesage/
    cli.py
    db.py
    strategic/
      context.py
      situation.py
      contradiction.py
      solvability.py
      timing.py
      commitment.py
      risk.py
      confidence.py
      advisor.py
      memory.py
      calibration.py
      retrieval.py
      patterns.py
      pattern_memory.py
      pattern_retrieval.py
      pipeline.py
      schemas.py
```

## Current Status

Version: v0.8.1

Implemented:

- Strategic Judgment
- Judgment Review
- SQLite Memory
- Lesson Retrieval
- Strategic Pattern Retrieval

Not Implemented:

- LLM reasoning
- Embedding retrieval
- Autonomous execution
- External tools

## Design Principles

- Current facts override historical memory.
- Strategic patterns are not facts.
- Strategic patterns are not predictions.
- Candidate lessons can remind, not decide.
- OneSage should protect long-term resources.
- Every recommendation should include stop conditions.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Pre-release Check](docs/GitHub_PreRelease_Check.md)
