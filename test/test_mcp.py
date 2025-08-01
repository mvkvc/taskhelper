import pytest
from taskhelper.mcp import mcp

pytestmark = pytest.mark.anyio


@pytest.fixture
def mcp_client():
    return mcp


def extract_structured_data(result):
    assert isinstance(result, tuple)
    assert len(result) == 2
    _, data = result
    return data["result"] if isinstance(data, dict) and "result" in data else data


async def test_create_task(mcp_client):
    result = await mcp_client.call_tool(
        "create_task",
        {
            "title": "Test Task",
            "priority": "high",
            "complexity": "medium",
            "description": "Test description",
        },
    )
    data = extract_structured_data(result)
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"
    assert data["complexity"] == "medium"
    assert data["description"] == "Test description"
    assert data["status"] == "todo"


async def test_get_task(mcp_client):
    create_result = await mcp_client.call_tool(
        "create_task",
        {"title": "Test Task for Get", "priority": "medium", "complexity": "low"},
    )
    task_id = extract_structured_data(create_result)["id"]
    result = await mcp_client.call_tool("get_task", {"task_id": task_id})
    data = extract_structured_data(result)
    assert data["id"] == task_id
    assert data["title"] == "Test Task for Get"


async def test_list_tasks(mcp_client):
    await mcp_client.call_tool(
        "create_task",
        {
            "title": "List Task 1",
            "priority": "low",
            "complexity": "low",
            "status": "todo",
        },
    )
    await mcp_client.call_tool(
        "create_task",
        {
            "title": "List Task 2",
            "priority": "medium",
            "complexity": "medium",
            "status": "inprogress",
        },
    )

    result = await mcp_client.call_tool("list_tasks", {})
    data = extract_structured_data(result)
    data = data if isinstance(data, list) else data["result"]
    assert len([t for t in data if t["status"] == "todo"]) >= 1
    assert len([t for t in data if t["status"] == "inprogress"]) >= 1

    result = await mcp_client.call_tool("list_tasks", {"statuses": ["todo"]})
    data = extract_structured_data(result)
    data = data if isinstance(data, list) else data["result"]
    assert all(t["status"] == "todo" for t in data)


async def test_update_task(mcp_client):
    create_result = await mcp_client.call_tool(
        "create_task",
        {"title": "Task to Update", "priority": "low", "complexity": "low"},
    )
    task_id = extract_structured_data(create_result)["id"]
    result = await mcp_client.call_tool(
        "update_task",
        {
            "task_id": task_id,
            "title": "Updated Task Title",
            "description": "Updated description",
            "status": "inprogress",
            "priority": "high",
        },
    )
    data = extract_structured_data(result)
    assert data["id"] == task_id
    assert data["title"] == "Updated Task Title"
    assert data["description"] == "Updated description"
    assert data["status"] == "inprogress"
    assert data["priority"] == "high"


async def test_delete_task(mcp_client):
    create_result = await mcp_client.call_tool(
        "create_task",
        {"title": "Task to Delete", "priority": "low", "complexity": "low"},
    )
    task_id = extract_structured_data(create_result)["id"]
    result = await mcp_client.call_tool("delete_task", {"task_id": task_id})
    data = extract_structured_data(result)
    assert data["id"] == task_id
    get_result = await mcp_client.call_tool("get_task", {"task_id": task_id})
    assert extract_structured_data(get_result) is None
