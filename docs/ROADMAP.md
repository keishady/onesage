# OneSage Roadmap

## Current: v0.8.1

OneSage is currently an alpha-stage Strategic Intelligence Skill.

Implemented:

- deterministic Strategic Judgment pipeline
- Judgment Review
- Error Taxonomy
- Confidence Update
- SQLite-backed Judgment Memory
- Lesson Memory
- Lesson Retrieval
- Strategic Pattern Data Layer
- Strategic Pattern Retrieval
- Pattern Audit records

Not implemented:

- LLM-assisted reasoning
- embedding retrieval
- autonomous execution
- external tool execution
- browser automation
- workflow orchestration

## v0.8.x Alpha Stabilization

Goal: make the current deterministic strategic core easier to test, inspect, and contribute to.

Planned work:

- improve README and examples
- add test fixtures for strategic cases
- add deterministic regression tests
- improve JSON schema documentation
- improve CLI examples
- improve Pattern Audit review
- document database schema

Non-goals:

- no external APIs
- no browser automation
- no shell automation
- no autonomous execution

## v0.9 LLM-assisted Reasoning

Goal: allow LLMs to assist reasoning while preserving OneSage's strategic discipline.

Potential work:

- optional LLM-assisted context extraction
- optional LLM-assisted contradiction analysis
- optional narrative explanation generation
- guardrails for facts vs assumptions vs unknowns
- evaluation against deterministic baseline

Rules:

- LLM output must not replace facts.
- LLM output must expose uncertainty.
- Deterministic safety and governance rules remain authoritative.
- Pattern and Lesson memory remain probabilistic references.

Non-goals:

- no autonomous tool execution
- no hidden action-taking
- no workflow engine

## v1.0 Stable Strategic Skill

Goal: provide a stable embeddable strategic skill for humans and AI agents.

Expected capabilities:

- stable StrategicJudgment schema
- stable JudgmentReview schema
- stable Pattern schema
- documented SQLite schema
- tested CLI
- stable contribution process for cases, lessons, and patterns
- clear integration guide for other agents

Expected guarantees:

- current facts override memory and patterns
- no automatic external execution
- all recommendations include stop conditions
- confidence remains explainable
- Pattern influence boundaries are enforced

## Long-term Direction

OneSage should become a reusable strategic reasoning layer that can be embedded in other AI systems.

It should help answer:

- Should this be done?
- Should this wait?
- Should this be tested first?
- What is the main contradiction?
- What is the minimum next action?
- When should we stop?

It should not become a general automation platform.

