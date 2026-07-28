from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from .audit import recent_events, record_event
from .core.onesage64gua import apply_moving_line, get_gua, load_gua_templates, phase_mapping
from .db import connect, init_db, now
from .execution_kernel import execute
from .growth_kernel import review
from .method_kernel import decide
from .model_router import route_for
from .objection_kernel import OVERRIDE_PHRASE, override_allowed
from .safety import validate_skill_file
from .schemas import Decision, ModelRole, RiskLevel, WorkflowSpec
from .strategic.calibration import render_review_markdown, review_judgment
from .strategic.memory import load_judgment, save_review_and_lesson
from .strategic.pattern_memory import list_patterns, search_patterns
from .strategic.pipeline import render_json, render_markdown, strategize
from .strategic.retrieval import list_lessons, search_lessons
from .workspace import DEFAULT_WORKSPACE, init_workspace


def print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_panel(title: str, body: str) -> None:
    print(f"\n== {title} ==\n{body}\n")


def load_decision(conn, decision_id: int) -> Decision:
    row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
    if not row:
        raise SystemExit("Decision not found.")
    return Decision.model_validate_json(row["decision_json"])


def cmd_init(_args) -> None:
    path = init_workspace()
    init_db()
    record_event("workspace_initialized", {"path": str(path)})
    print_panel("OK", f"OneSage v0.4 initialized at {path}")


def cmd_project_create(args) -> None:
    init_db()
    conn = connect()
    conn.execute(
        "INSERT OR REPLACE INTO projects (id, objective, created_at) VALUES (?, ?, ?)",
        (args.project_id, args.objective, now()),
    )
    conn.commit()
    conn.close()
    record_event("project_created", {"objective": args.objective}, project_id=args.project_id)
    print_panel("OK", f"Project created: {args.project_id}\nObjective: {args.objective}")


def cmd_decide(args) -> None:
    init_db()
    decision = decide(args.project_id, args.command, prefer_mercury=args.prefer_mercury)
    conn = connect()
    cur = conn.execute(
        """
        INSERT INTO decisions
        (project_id, raw_command, decision_json, action_type, objection_required, override_allowed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.project_id,
            args.command,
            decision.model_dump_json(),
            decision.action_type.value,
            int(decision.objection_required),
            int(decision.override_allowed),
            now(),
        ),
    )
    conn.commit()
    decision_id = int(cur.lastrowid)
    conn.close()

    record_event(
        "decision_created",
        {
            "action_type": decision.action_type.value,
            "risk_level": decision.risk_level.value,
            "should_act_now": decision.should_act_now,
            "policy": decision.policy.model_dump() if decision.policy else None,
        },
        project_id=args.project_id,
        decision_id=decision_id,
    )

    print_panel("OneSage Decision", f"Decision ID: {decision_id}")
    print_json(decision.model_dump())
    if decision.objection_required:
        print_panel(
            "Objection",
            "OneSage 不建议直接执行。\n\n"
            f"如果该动作允许 override，请运行：\n"
            f"python -m onesage.cli override {decision_id} \"{OVERRIDE_PHRASE}\"",
        )


def cmd_should_act_now(args) -> None:
    decision = decide(args.project_id, args.command)
    print_json(
        {
            "should_act_now": decision.should_act_now,
            "risk_level": decision.risk_level.value,
            "action_type": decision.action_type.value,
            "minimum_next_action": decision.minimum_next_action,
            "policy": decision.policy.model_dump() if decision.policy else None,
        }
    )


def cmd_strategize(args) -> None:
    judgment = strategize(args.question, project_id=args.project_id, domain=args.domain, save=args.save)
    if args.json:
        print(render_json(judgment))
    else:
        if args.save:
            print(f"Saved Judgment ID: {judgment.judgment_id}\n")
        print(render_markdown(judgment))
        if judgment.relevant_memory.matches:
            print_panel(
                "Strategic Memory",
                "\n".join(
                    [
                        f"Retrieved memories: {len(judgment.relevant_memory.matches)}",
                        f"Confidence adjustment: {judgment.relevant_memory.confidence_adjustment}",
                        *[
                            (
                                f"- score={match.similarity_score} status={match.lesson_status} "
                                f"judgment={match.judgment_id} risk={match.largest_risk}"
                            )
                            for match in judgment.relevant_memory.matches[:5]
                        ],
                    ]
                ),
            )
        if judgment.relevant_patterns.matched_patterns:
            print_panel(
                "Relevant Strategic Patterns",
                "\n".join(
                    [
                        f"Matched patterns: {len(judgment.relevant_patterns.matched_patterns)}",
                        f"Confidence adjustment: {judgment.relevant_patterns.confidence_adjustment}",
                        *[
                            (
                                f"- score={match.match_score} status={match.status} "
                                f"pattern={match.pattern_id} risk={match.risk_type}"
                            )
                            for match in judgment.relevant_patterns.matched_patterns[:5]
                        ],
                        "Warnings:",
                        *[f"- {warning}" for warning in judgment.relevant_patterns.pattern_warnings[:5]],
                    ]
                ),
            )


def cmd_review(args) -> None:
    try:
        judgment = load_judgment(args.judgment_id)
    except KeyError as exc:
        raise SystemExit(str(exc)) from exc
    review_result = review_judgment(judgment, args.actual_outcome)
    save_review_and_lesson(review_result, judgment)
    if args.json:
        print(json.dumps(review_result.model_dump(), ensure_ascii=False, indent=2))
    else:
        print(render_review_markdown(review_result))


def cmd_memory_list(args) -> None:
    lessons = list_lessons()
    if args.json:
        print_json(
            {
                "count": len(lessons),
                "lessons": lessons,
            }
        )
        return
    print_panel("Strategic Memory", f"Lesson count: {len(lessons)}")
    for lesson in lessons:
        print(
            f"[{lesson['id']}] status={lesson['status']} domain={lesson['domain']} "
            f"judgment={lesson.get('judgment_id')} source_review={lesson['source_review_id']}"
        )
        print(f"scope: {lesson.get('scope', '')}")
        print(f"lesson: {lesson['lesson']}\n")


def cmd_memory_search(args) -> None:
    lessons = search_lessons(args.query, limit=args.limit)
    if args.json:
        print_json(
            {
                "query": args.query,
                "count": len(lessons),
                "lessons": lessons,
            }
        )
        return
    print_panel("Strategic Memory Search", f"Query: {args.query}\nMatches: {len(lessons)}")
    for lesson in lessons:
        print(
            f"[{lesson['id']}] score={lesson['similarity_score']} "
            f"status={lesson['status']} domain={lesson['domain']} judgment={lesson.get('judgment_id')}"
        )
        print(f"scope: {lesson.get('scope', '')}")
        print(f"lesson: {lesson['lesson']}\n")


def cmd_pattern_list(args) -> None:
    patterns = list_patterns()
    if args.json:
        print_json(
            {
                "count": len(patterns),
                "patterns": patterns,
            }
        )
        return
    print_panel("Strategic Patterns", f"Pattern count: {len(patterns)}")
    for pattern in patterns:
        print(
            f"[{pattern['id']}] status={pattern['status']} domain={pattern['domain']} "
            f"confidence={pattern['confidence']} risk={pattern['risk_type']}"
        )
        print(
            f"pattern_id: {pattern['pattern_id']}\n"
            f"stage: {pattern['situation_stage']} contradiction: {pattern['contradiction_type']} "
            f"commitment: {pattern['commitment_level']}\n"
            f"supporting_lessons: {pattern.get('supporting_lessons', [])}\n"
        )


def cmd_pattern_search(args) -> None:
    patterns = search_patterns(args.query, limit=args.limit)
    if args.json:
        print_json(
            {
                "query": args.query,
                "count": len(patterns),
                "patterns": patterns,
            }
        )
        return
    print_panel("Strategic Pattern Search", f"Query: {args.query}\nMatches: {len(patterns)}")
    for pattern in patterns:
        print(
            f"[{pattern['id']}] score={pattern['similarity_score']} "
            f"status={pattern['status']} domain={pattern['domain']} confidence={pattern['confidence']}"
        )
        print(
            f"pattern_id: {pattern['pattern_id']}\n"
            f"risk: {pattern['risk_type']} contradiction: {pattern['contradiction_type']}\n"
        )


def cmd_override(args) -> None:
    init_db()
    conn = connect()
    decision = load_decision(conn, args.decision_id)
    ok, msg = override_allowed(decision, args.phrase)
    if not ok:
        record_event("override_rejected", {"message": msg}, project_id=decision.project_id, decision_id=args.decision_id, actor="user")
        conn.close()
        print_panel("Override Rejected", msg)
        raise SystemExit(1)

    result = execute(decision, user_override=True, decision_id=args.decision_id)
    conn.execute(
        "UPDATE decisions SET user_override = 1, executed = ? WHERE id = ?",
        (int(result["executed"]), args.decision_id),
    )
    conn.commit()
    conn.close()
    record_event("override_accepted", {"phrase": "matched"}, project_id=decision.project_id, decision_id=args.decision_id, actor="user")
    print_panel("OK", "Override accepted. Execution simulated.")
    print_json(result)


def cmd_execute(args) -> None:
    init_db()
    conn = connect()
    decision = load_decision(conn, args.decision_id)
    result = execute(decision, user_override=False, decision_id=args.decision_id)
    conn.execute(
        "UPDATE decisions SET executed = ? WHERE id = ?",
        (int(result["executed"]), args.decision_id),
    )
    conn.commit()
    conn.close()
    print_json(result)


def cmd_outcome(args) -> None:
    init_db()
    conn = connect()
    decision = load_decision(conn, args.decision_id)
    result = review(decision, args.actual_outcome, args.score)

    conn.execute(
        "INSERT INTO outcomes (decision_id, actual_outcome, score, review_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (args.decision_id, args.actual_outcome, args.score, json.dumps(result, ensure_ascii=False), now()),
    )
    rule = result["rule_candidate"]
    conn.execute(
        """
        INSERT INTO rules
        (name, description, trigger_condition, action_effect, status, evidence_count, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rule["name"],
            rule["description"],
            rule["trigger_condition"],
            rule["action_effect"],
            rule["status"],
            1,
            now(),
            now(),
        ),
    )
    memory = result["memory_update"]
    conn.execute(
        """
        INSERT INTO memory_lessons
        (project_id, source_decision_id, lesson, scope, confidence, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            decision.project_id,
            args.decision_id,
            memory["lesson"],
            memory["scope"],
            memory["confidence"],
            memory["status"],
            now(),
        ),
    )
    conn.execute(
        "INSERT INTO growth_logs (project_id, growth_type, content, source_decision_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (decision.project_id, "outcome_review", json.dumps(result["review_report"], ensure_ascii=False), args.decision_id, "recorded", now()),
    )
    conn.commit()
    conn.close()
    record_event("outcome_reviewed", result, project_id=decision.project_id, decision_id=args.decision_id)
    print_panel("Growth Kernel", "Outcome recorded. Review and memory candidate generated.")
    print_json(result)


def cmd_growth(_args) -> None:
    init_db()
    conn = connect()
    logs = conn.execute("SELECT * FROM growth_logs ORDER BY id DESC LIMIT 10").fetchall()
    rules = conn.execute("SELECT * FROM rules ORDER BY id DESC LIMIT 10").fetchall()
    memories = conn.execute("SELECT * FROM memory_lessons ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    print_json(
        {
            "growth_logs": [dict(row) for row in logs],
            "rule_candidates": [dict(row) for row in rules],
            "memory_candidates": [dict(row) for row in memories],
        }
    )


def cmd_trace(args) -> None:
    print_json(recent_events(limit=args.limit))


def cmd_skill_validate(args) -> None:
    manifest, sandbox = validate_skill_file(args.path)
    record_event(
        "skill_sandboxed",
        {
            "path": str(args.path),
            "manifest": manifest.model_dump() if manifest else None,
            "sandbox": sandbox.model_dump(),
        },
    )
    print_json(sandbox.model_dump())


def cmd_skill_install(args) -> None:
    init_db()
    manifest, sandbox = validate_skill_file(args.path)
    if manifest is None:
        print_json(sandbox.model_dump())
        raise SystemExit(1)
    if args.enable and not sandbox.accepted:
        print_panel("Blocked", "Skill was not accepted by sandbox; refusing to enable.")
        print_json(sandbox.model_dump())
        raise SystemExit(1)

    manifest.enabled = bool(args.enable and sandbox.accepted)
    conn = connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO skill_manifests
        (name, manifest_json, sandbox_json, enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM skill_manifests WHERE name = ?), ?), ?)
        """,
        (
            manifest.name,
            manifest.model_dump_json(),
            sandbox.model_dump_json(),
            int(manifest.enabled),
            manifest.name,
            now(),
            now(),
        ),
    )
    conn.commit()
    conn.close()
    record_event("skill_installed", {"manifest": manifest.model_dump(), "sandbox": sandbox.model_dump()})
    print_json({"installed": True, "enabled": manifest.enabled, "sandbox": sandbox.model_dump()})


def cmd_skill_list(_args) -> None:
    init_db()
    conn = connect()
    rows = conn.execute("SELECT * FROM skill_manifests ORDER BY name").fetchall()
    conn.close()
    print_json(
        [
            {
                "name": row["name"],
                "enabled": bool(row["enabled"]),
                "manifest": json.loads(row["manifest_json"]),
                "sandbox": json.loads(row["sandbox_json"]),
            }
            for row in rows
        ]
    )


def cmd_workflow_save(args) -> None:
    init_db()
    workflow = WorkflowSpec.model_validate_json(args.path.read_text(encoding="utf-8"))
    conn = connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO workflows
        (name, workflow_json, status, created_at, updated_at)
        VALUES (?, ?, ?, COALESCE((SELECT created_at FROM workflows WHERE name = ?), ?), ?)
        """,
        (workflow.name, workflow.model_dump_json(), "draft", workflow.name, now(), now()),
    )
    conn.commit()
    conn.close()
    record_event("workflow_saved", workflow.model_dump())
    print_json({"saved": True, "workflow": workflow.model_dump()})


def cmd_workflow_demo(_args) -> None:
    print_json(
        {
            "name": "safe_customer_outreach_test",
            "objective": "Test a small customer outreach batch before any external write expansion.",
            "steps": [
                {
                    "name": "collect_facts",
                    "action_type": "observe",
                    "required_permissions": ["read_local"],
                    "safety_gate": "facts_and_success_metric_present",
                    "retry_policy": "manual",
                    "evaluation_check": "at_least_three_confirmed_facts",
                },
                {
                    "name": "draft_message",
                    "action_type": "test",
                    "required_permissions": ["write_local"],
                    "safety_gate": "local_only",
                    "retry_policy": "manual",
                    "evaluation_check": "human_reviewed",
                },
            ],
            "inputs": {},
            "outputs": {},
            "review_required": True,
        }
    )


def cmd_model_route(args) -> None:
    print_json(route_for(args.role, risk_level=args.risk_level, prefer_mercury=args.prefer_mercury).model_dump())


def cmd_gua_show(args) -> None:
    identifier = int(args.identifier) if str(args.identifier).isdigit() else args.identifier
    template = get_gua(identifier)
    data = template.to_dict()
    if args.compact:
        data = {
            "gua_name": template.gua_name,
            "gua_number": template.gua_number,
            "initial_state_vector": template.initial_state_vector,
            "phase_mapping": phase_mapping(template),
            "trend_prediction": template.trend_prediction,
            "source_reference": template.source_reference,
        }
    print_json(data)


def cmd_gua_line(args) -> None:
    identifier = int(args.identifier) if str(args.identifier).isdigit() else args.identifier
    moving_line = int(args.moving_line) if str(args.moving_line).isdigit() else args.moving_line
    template = get_gua(identifier)
    print_json(apply_moving_line(template, moving_line))


def cmd_gua_list(_args) -> None:
    print_json(
        [
            {
                "gua_number": template.gua_number,
                "gua_name": template.gua_name,
                "trend_prediction": template.trend_prediction,
            }
            for template in load_gua_templates()
        ]
    )


def cmd_doctor(_args) -> None:
    init_workspace()
    init_db()
    checks = {
        "workspace": str(DEFAULT_WORKSPACE),
        "permissions_json": (DEFAULT_WORKSPACE / "permissions.json").exists(),
        "method_prompt": (DEFAULT_WORKSPACE / "METHOD.md").exists(),
        "soul_prompt": (DEFAULT_WORKSPACE / "SOUL.md").exists(),
        "example_skill": (DEFAULT_WORKSPACE / "sandbox_skills" / "local_summary.skill.json").exists(),
        "onesage64gua_records": len(load_gua_templates()),
    }
    print_json(checks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onesage", description="OneSage v0.4 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    sub.add_parser("growth").set_defaults(func=cmd_growth)

    trace = sub.add_parser("trace")
    trace.add_argument("--limit", type=int, default=20)
    trace.set_defaults(func=cmd_trace)

    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_create = project_sub.add_parser("create")
    project_create.add_argument("project_id")
    project_create.add_argument("objective")
    project_create.set_defaults(func=cmd_project_create)

    decide_parser = sub.add_parser("decide")
    decide_parser.add_argument("project_id")
    decide_parser.add_argument("command")
    decide_parser.add_argument("--prefer-mercury", action="store_true")
    decide_parser.set_defaults(func=cmd_decide)

    now_parser = sub.add_parser("should-act-now")
    now_parser.add_argument("project_id")
    now_parser.add_argument("command")
    now_parser.set_defaults(func=cmd_should_act_now)

    strategize_parser = sub.add_parser("strategize")
    strategize_parser.add_argument("question")
    strategize_parser.add_argument("--project-id")
    strategize_parser.add_argument("--domain")
    strategize_parser.add_argument("--save", action="store_true")
    strategize_parser.add_argument("--json", action="store_true")
    strategize_parser.set_defaults(func=cmd_strategize)

    review_parser = sub.add_parser("review")
    review_parser.add_argument("judgment_id")
    review_parser.add_argument("actual_outcome")
    review_parser.add_argument("--json", action="store_true")
    review_parser.set_defaults(func=cmd_review)

    memory = sub.add_parser("memory")
    memory_sub = memory.add_subparsers(dest="memory_command", required=True)
    memory_list = memory_sub.add_parser("list")
    memory_list.add_argument("--json", action="store_true")
    memory_list.set_defaults(func=cmd_memory_list)
    memory_search = memory_sub.add_parser("search")
    memory_search.add_argument("query")
    memory_search.add_argument("--limit", type=int, default=10)
    memory_search.add_argument("--json", action="store_true")
    memory_search.set_defaults(func=cmd_memory_search)

    pattern = sub.add_parser("pattern")
    pattern_sub = pattern.add_subparsers(dest="pattern_command", required=True)
    pattern_list = pattern_sub.add_parser("list")
    pattern_list.add_argument("--json", action="store_true")
    pattern_list.set_defaults(func=cmd_pattern_list)
    pattern_search = pattern_sub.add_parser("search")
    pattern_search.add_argument("query")
    pattern_search.add_argument("--limit", type=int, default=10)
    pattern_search.add_argument("--json", action="store_true")
    pattern_search.set_defaults(func=cmd_pattern_search)

    override_parser = sub.add_parser("override")
    override_parser.add_argument("decision_id", type=int)
    override_parser.add_argument("phrase")
    override_parser.set_defaults(func=cmd_override)

    execute_parser = sub.add_parser("execute")
    execute_parser.add_argument("decision_id", type=int)
    execute_parser.set_defaults(func=cmd_execute)

    outcome_parser = sub.add_parser("outcome")
    outcome_parser.add_argument("decision_id", type=int)
    outcome_parser.add_argument("actual_outcome")
    outcome_parser.add_argument("--score", type=float, required=True)
    outcome_parser.set_defaults(func=cmd_outcome)

    skill = sub.add_parser("skill")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_validate = skill_sub.add_parser("validate")
    skill_validate.add_argument("path", type=Path)
    skill_validate.set_defaults(func=cmd_skill_validate)
    skill_install = skill_sub.add_parser("install")
    skill_install.add_argument("path", type=Path)
    skill_install.add_argument("--enable", action="store_true")
    skill_install.set_defaults(func=cmd_skill_install)
    skill_sub.add_parser("list").set_defaults(func=cmd_skill_list)

    workflow = sub.add_parser("workflow")
    workflow_sub = workflow.add_subparsers(dest="workflow_command", required=True)
    workflow_save = workflow_sub.add_parser("save")
    workflow_save.add_argument("path", type=Path)
    workflow_save.set_defaults(func=cmd_workflow_save)
    workflow_sub.add_parser("demo").set_defaults(func=cmd_workflow_demo)

    model = sub.add_parser("model")
    model_sub = model.add_subparsers(dest="model_command", required=True)
    route = model_sub.add_parser("route")
    route.add_argument("role", type=ModelRole)
    route.add_argument("--risk-level", type=RiskLevel, default=RiskLevel.L1_WRITE_LOCAL)
    route.add_argument("--prefer-mercury", action="store_true")
    route.set_defaults(func=cmd_model_route)

    gua = sub.add_parser("gua")
    gua_sub = gua.add_subparsers(dest="gua_command", required=True)
    gua_show = gua_sub.add_parser("show")
    gua_show.add_argument("identifier", help="Gua number or name, e.g. 1 or 乾")
    gua_show.add_argument("--compact", action="store_true")
    gua_show.set_defaults(func=cmd_gua_show)
    gua_line = gua_sub.add_parser("line")
    gua_line.add_argument("identifier", help="Gua number or name, e.g. 1 or 乾")
    gua_line.add_argument("moving_line", help="1-6 or 用九/用六")
    gua_line.set_defaults(func=cmd_gua_line)
    gua_sub.add_parser("list").set_defaults(func=cmd_gua_list)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
