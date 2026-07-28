# OneSage Architecture

Version: v0.8.1

OneSage is a Strategic Intelligence Skill: a decision layer before action.

It is designed to help humans and AI agents reason about strategic questions before committing resources.

OneSage is not:

- an autonomous agent
- a tool executor
- a workflow engine
- a browser or shell automation layer

OneSage is:

- a strategic judgment core
- a calibration loop
- a memory system
- a pattern retrieval layer

## 1. Product Positioning

OneSage helps answer:

- What situation am I in?
- What is the main contradiction?
- Is the contradiction solvable by the user?
- Is now the right time to act?
- Should the user act, test, observe, or stop?
- What should be reviewed later?

The governing idea is:

```text
Decision Layer before Action
```

OneSage should improve decisions before execution begins.

## 2. Core Flow

```text
Question
|
v
StrategicContext
|
v
Lesson Retrieval
|
v
Pattern Retrieval
|
v
Situation Analysis
|
v
Contradiction Analysis
|
v
Solvability Analysis
|
v
Timing Analysis
|
v
Commitment Level
|
v
Strategic Risk
|
v
Confidence
|
v
Strategic Advice
|
v
Judgment Review
|
v
Lesson Memory
|
v
Pattern Memory
```

## 3. v0.5 Strategic Architecture

v0.5 redefined OneSage from an execution-oriented agent into a Strategic Intelligence Skill.

The core architecture:

```text
Input Context
|
v
Situation Analyzer
|
v
Contradiction Analyzer
|
v
Timing Analyzer
|
v
Decision Advisor
|
v
Strategic Memory
|
v
Review Engine
```

Main boundaries:

- OneSage analyzes strategy.
- OneSage does not execute tasks.
- OneSage does not orchestrate workflows.
- OneSage does not control tools.

## 4. v0.5.1 Soul Layer

v0.5.1 introduced strategic personality and judgment discipline.

Core principles:

- Do not flatter the user.
- Do not recommend continuing because of sunk cost.
- Do not recommend quitting because of one failure.
- Admit uncertainty when information is insufficient.
- Protect long-term resources.
- Every recommendation needs stop conditions.
- Separate facts, assumptions, and unknowns.

v0.5.1 also added:

- Solvability Analysis
- Strategic Commitment Level
- Strategic Risk categories

Strategic risks:

- direction risk
- timing risk
- resource risk
- sunk cost risk
- opportunity cost risk

## 5. v0.5.2 Judgment Calibration

v0.5.2 added the idea that OneSage should judge its own judgment.

Key principle:

```text
Success does not prove a judgment was correct.
Failure does not prove a judgment was wrong.
```

Calibration separates:

- judgment quality
- reasoning quality
- decision quality
- outcome influence

Error taxonomy:

- Fact Error
- Stage Error
- Contradiction Error
- Solvability Error
- Timing Error
- Commitment Error
- Strategic Risk Error
- Advice Error
- Calibration Error

## 6. v0.6 Strategic Judgment Core

v0.6 implemented the first runnable deterministic strategic judgment pipeline.

Implemented modules:

- `context.py`
- `situation.py`
- `contradiction.py`
- `solvability.py`
- `timing.py`
- `commitment.py`
- `risk.py`
- `confidence.py`
- `advisor.py`
- `pipeline.py`
- `schemas.py`

The output is a `StrategicJudgment` containing:

- Input Context
- Situation Analysis
- Contradiction Analysis
- Solvability Analysis
- Timing Analysis
- Commitment Level
- Strategic Risk
- Strategic Advice
- Confidence
- Review Plan

## 7. v0.6.1 Memory and Calibration

v0.6.1 added persistence and review:

- `strategic_judgments`
- `judgment_reviews`
- `strategic_lessons`

It enabled:

```text
Strategic judgment
|
v
Save to SQLite
|
v
Review actual outcome
|
v
Generate lesson candidate
```

Lesson status:

- candidate
- validated
- trusted
- expired
- rejected

## 8. v0.7 Memory Retrieval

v0.7 upgraded strategic memory from storage to judgment assistance.

Lesson retrieval uses deterministic matching:

- domain
- situation stage
- contradiction type
- commitment level
- risk type
- keyword overlap

Rules:

- Current facts override historical lessons.
- Candidate lessons can only remind.
- Validated or trusted lessons may affect confidence.
- Expired lessons do not participate.

## 9. v0.7.1 Pattern Architecture

v0.7.1 introduced the distinction between Lesson and Pattern.

Lesson:

- one reviewed experience
- generated from one judgment and one actual outcome
- can remind, not decide

Pattern:

- stable strategic regularity formed from multiple similar lessons
- probabilistic reference
- has applicability and counter examples
- can support future judgment cautiously

Pattern fields:

- pattern_id
- domain
- situation_stage
- contradiction_type
- commitment_level
- risk_type
- supporting_lessons
- confidence
- applicability
- counter_examples
- status

## 10. v0.7.2 Pattern Governance

v0.7.2 defined the governance rule:

```text
Current Facts > Strategic Pattern > Historical Lessons
```

Pattern is not:

- a rule
- a fact
- a prediction

Pattern is:

```text
a probabilistic strategic reference based on historical judgments
```

Pattern lifecycle:

```text
candidate
|
v
validated
|
v
trusted
|
v
challenged
|
v
expired
```

Pattern may influence:

- confidence
- reminders
- investigation questions
- minimum next action, only when trusted and only toward lower commitment

Pattern may not:

- replace facts
- directly change recommendation
- raise commitment level
- lower risk automatically

## 11. v0.8 Pattern Data and Retrieval

v0.8.0 implemented the Pattern data layer:

- `patterns.py`
- `pattern_memory.py`
- `strategic_patterns`
- `pattern_audit`

v0.8.1 integrated Pattern Retrieval into `strategize`.

Pattern retrieval is deterministic and matches:

- domain
- situation_stage
- contradiction_type
- commitment_level
- risk_type
- keyword overlap

Current integration rules:

- Pattern can add reminders.
- Pattern can add investigation questions.
- Validated or trusted Pattern can adjust confidence.
- Candidate Pattern only reminds.
- Pattern cannot directly change A/B/C/D recommendation.

## 12. Current Data Tables

Strategic memory tables:

- `strategic_judgments`
- `judgment_reviews`
- `strategic_lessons`

Pattern tables:

- `strategic_patterns`
- `pattern_audit`

Legacy v0.4 tables still exist and are not removed:

- `projects`
- `decisions`
- `outcomes`
- `rules`
- `growth_logs`
- `audit_events`
- `skill_manifests`
- `memory_lessons`
- `workflows`

## 13. Boundary

OneSage should remain a strategic reasoning layer.

It should not become:

- a general autonomous agent
- a tool marketplace
- a browser automation framework
- a shell executor
- a workflow platform

The long-term path is:

```text
better judgment
|
v
better review
|
v
better memory
|
v
better patterns
|
v
better future judgment
```

