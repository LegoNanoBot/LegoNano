"""Tests for worker client (against real supervisor API via TestClient)."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from unittest.mock import AsyncMock, MagicMock, patch

from nanobot.worker.client import SupervisorClient


def _make_mock_response(json_data, status_code=200):
    """Create a mock that behaves like httpx.Response (sync .json())."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_client_register():
    """Test the client sends well-formed registration request."""
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({
        "ok": True,
        "worker": {"worker_id": "w-test", "name": "tester", "status": "online"},
    })

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)) as mock_post:
        result = await client.register("tester", capabilities=["code"])
        mock_post.assert_called_once_with(
            "/api/v1/supervisor/workers/register",
            json={
                "worker_id": "w-test",
                "name": "tester",
                "capabilities": ["code"],
            },
        )
        assert result["ok"] is True

    await client.close()


@pytest.mark.asyncio
async def test_client_heartbeat():
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({"ok": True, "worker": {"status": "online"}})

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)) as mock_post:
        await client.heartbeat(current_task_id="t1", status="busy")
        mock_post.assert_called_once_with(
            "/api/v1/supervisor/workers/w-test/heartbeat",
            json={"current_task_id": "t1", "status": "busy"},
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_claim_task_none():
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({"ok": True, "task": None})

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)):
        result = await client.claim_task()
        assert result is None

    await client.close()


@pytest.mark.asyncio
async def test_client_claim_task_found():
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({
        "ok": True,
        "task": {"task_id": "t1", "instruction": "do stuff"},
    })

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)):
        result = await client.claim_task()
        assert result is not None
        assert result["task_id"] == "t1"

    await client.close()


@pytest.mark.asyncio
async def test_client_report_progress():
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({"ok": True})

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)) as mock_post:
        await client.report_progress("t1", iteration=2, message="halfway")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/api/v1/supervisor/tasks/t1/progress"

    await client.close()


@pytest.mark.asyncio
async def test_client_report_result():
    client = SupervisorClient("http://localhost:9200", "w-test")
    mock_response = _make_mock_response({"ok": True})

    with patch.object(client._client, "post", AsyncMock(return_value=mock_response)) as mock_post:
        await client.report_result("t1", status="completed", result="done")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["status"] == "completed"
        assert call_args[1]["json"]["result"] == "done"

    await client.close()


@pytest.mark.asyncio
async def test_client_unregister_graceful():
    """Unregister should not raise even if the supervisor is unreachable."""
    client = SupervisorClient("http://localhost:9200", "w-test")

    with patch.object(client._client, "delete", AsyncMock(side_effect=Exception("connection refused"))):
        await client.unregister()  # Should not raise

    await client.close()
