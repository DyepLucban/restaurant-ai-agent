import asyncio
import json
from uuid import uuid4

from agents.core import TOOL_LOG
from agents.orchestrator_agent import run


def args_match(actual: dict, expected: dict) -> bool:
    return all(actual.get(k) == v for k, v in expected.items())


def check(case: dict, answer: str, calls: list) -> list[str]:
    """Return a list of failure reasons (empty list = pass)."""
    low = answer.lower()
    fails = []

    for s in case.get("must_contain", []):
        if s.lower() not in low:
            fails.append(f"missing '{s}'")
    for s in case.get("must_not_contain", []):
        if s.lower() in low:
            fails.append(f"contains forbidden '{s}'")
    if case.get("must_contain_any") and not any(s.lower() in low for s in case["must_contain_any"]):
        fails.append(f"none of {case['must_contain_any']} found")

    for exp in case.get("expect_tool_calls", []):
        if not any(c["name"] == exp["name"] and args_match(c["args"], exp.get("args", {})) for c in calls):
            fails.append(f"expected tool call {exp} not found")
    if case.get("expect_no_tool_calls") and calls:
        fails.append(f"expected no tool calls, got {[c['name'] for c in calls]}")

    return fails


async def run_case(case: dict) -> tuple[str, list]:
    session_id = str(uuid4())                      # fresh session per case
    turns = case.get("turns") or [case["query"]]
    answer, calls = "", []
    for turn in turns:
        calls = []                                 # keep only the last turn's calls
        TOOL_LOG.set(calls)
        answer = await run(turn, session_id)
    return answer, calls


async def main():
    cases = json.load(open("evals/cases.json"))
    passed = 0
    for case in cases:
        answer, calls = await run_case(case)
        fails = check(case, answer, calls)
        passed += not fails
        print(f"{'PASS' if not fails else 'FAIL'} | {case.get('id', case.get('query'))}")
        if fails:
            print(f"     reasons: {fails}")
            print(f"     tools:   {[(c['name'], c['args']) for c in calls]}")
            print(f"     answer:  {answer[:150]}")
    print(f"\n{passed}/{len(cases)} passed")


asyncio.run(main())