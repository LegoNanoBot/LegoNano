"""Tests for supervisor planner."""

from __future__ import annotations

import pytest

from nanobot.providers.base import LLMProvider, LLMResponse
from nanobot.supervisor.planner import generate_plan


class MockPlannerProvider(LLMProvider):
    def __init__(self, response: str | None) -> None:
        super().__init__()
        self._response = response
        self.calls: list[list[dict]] = []

    async def chat(self, messages, tools=None, model=None, **kwargs) -> LLMResponse:
        self.calls.append(list(messages))
        return LLMResponse(content=self._response)

    def get_default_model(self) -> str:
        return "mock-model"


@pytest.mark.asyncio
async def test_generate_plan_returns_none_for_simple_request():
    provider = MockPlannerProvider('{"needs_plan": false}')

    plan = await generate_plan(provider, "mock-model", "say hello")

    assert plan is None
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_generate_plan_returns_multistep_plan_with_dependencies():
    provider = MockPlannerProvider(
        """
        {
          "needs_plan": true,
          "title": "Auth Refactor",
          "goal": "Refactor auth module safely",
          "steps": [
            {"index": 0, "label": "Inspect", "instruction": "Inspect current auth module", "depends_on": []},
            {"index": 1, "label": "Implement", "instruction": "Implement refactor", "depends_on": [0]}
          ]
        }
        """.strip()
    )

    plan = await generate_plan(
        provider,
        "mock-model",
        "refactor auth module",
        origin_channel="telegram",
        origin_chat_id="chat-1",
        session_key="session-1",
    )

    assert plan is not None
    assert plan.title == "Auth Refactor"
    assert plan.goal == "Refactor auth module safely"
    assert plan.origin_channel == "telegram"
    assert plan.origin_chat_id == "chat-1"
    assert plan.session_key == "session-1"
    assert [step.index for step in plan.steps] == [0, 1]
    assert plan.steps[0].depends_on == []
    assert plan.steps[1].depends_on == [0]


@pytest.mark.asyncio
async def test_generate_plan_returns_none_for_invalid_json():
    provider = MockPlannerProvider("definitely not json")

    plan = await generate_plan(provider, "mock-model", "complex request")

    assert plan is None


@pytest.mark.asyncio
async def test_generate_plan_parses_json_wrapped_in_code_fence():
    provider = MockPlannerProvider(
        """
        ```json
        {
          "needs_plan": true,
          "title": "Fenced Plan",
          "goal": "Parse fenced JSON",
          "steps": [
            {"index": 0, "instruction": "step 0", "depends_on": []}
          ]
        }
        ```
        """.strip()
    )

    plan = await generate_plan(provider, "mock-model", "parse fenced json")

    assert plan is not None
    assert plan.title == "Fenced Plan"
    assert len(plan.steps) == 1
    assert plan.steps[0].instruction == "step 0"


@pytest.mark.asyncio
async def test_generate_plan_returns_none_for_empty_steps():
    provider = MockPlannerProvider(
        '{"needs_plan": true, "title": "Empty", "goal": "No steps", "steps": []}'
    )

    plan = await generate_plan(provider, "mock-model", "empty plan")

    assert plan is None