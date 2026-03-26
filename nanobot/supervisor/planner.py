"""Planner — decides whether a request needs a multi-step plan.

The planner uses the LLM to analyze incoming requests and either:
1. Pass them through (simple requests)
2. Generate a Plan with multiple steps and dependencies (complex requests)

This is used by the supervisor agent loop to intercept complex tasks
before they hit the regular dispatch path.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from nanobot.supervisor.models import Plan, PlanStep


PLAN_SYSTEM_PROMPT = """\
You are a task planner. Given a user request, decide if it requires multiple
independent steps that can be executed in parallel by different workers, or if it
can be handled as a single task.

If the request is simple (can be done in one step), respond with:
{"needs_plan": false}

If the request is complex, respond with a plan:
{
  "needs_plan": true,
  "title": "Short plan title",
  "goal": "What the user wants to achieve",
  "steps": [
    {"index": 0, "label": "Step label", "instruction": "Detailed instruction", "depends_on": []},
    {"index": 1, "label": "Step label", "instruction": "Detailed instruction", "depends_on": [0]}
  ]
}

Rules:
- Each step should be independently executable by a worker agent with file/shell/web tools.
- Use depends_on to express ordering constraints (list of step indices that must complete first).
- Steps with no dependencies can run in parallel.
- Keep steps concrete and actionable.
- Respond ONLY with valid JSON, no other text.
"""


async def generate_plan(
    provider: Any,
    model: str,
    user_request: str,
    origin_channel: str = "cli",
    origin_chat_id: str = "direct",
    session_key: str | None = None,
) -> Plan | None:
    """Ask the LLM to produce a plan for a user request.

    Returns a Plan if the request is complex, None if it's simple.
    """
    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": user_request},
    ]

    response = await provider.chat_with_retry(
        messages=messages,
        model=model,
    )

    if not response.content:
        return None

    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code fences
        content = response.content.strip()
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                try:
                    data = json.loads(cleaned)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                logger.warning("Planner returned non-JSON response")
                return None
        else:
            logger.warning("Planner returned non-JSON response")
            return None

    if not data.get("needs_plan", False):
        return None

    steps = []
    for s in data.get("steps", []):
        steps.append(PlanStep(
            index=s["index"],
            instruction=s["instruction"],
            label=s.get("label", ""),
            depends_on=s.get("depends_on", []),
        ))

    if not steps:
        return None

    plan = Plan(
        title=data.get("title", "Untitled Plan"),
        goal=data.get("goal", user_request),
        steps=steps,
        origin_channel=origin_channel,
        origin_chat_id=origin_chat_id,
        session_key=session_key,
    )
    logger.info("Planner generated plan '{}' with {} steps", plan.title, len(steps))
    return plan
