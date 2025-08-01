import logging

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .db import (
    init_db_with_data,
    create_task as db_create_task,
    get_task as db_get_task,
    list_tasks as db_list_tasks,
    update_task as db_update_task,
    delete_task as db_delete_task,
)
from .task import Task, TaskCreate, TaskUpdate, Status, Priority, Complexity

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)

mcp = FastMCP("taskhelper", log_level=get_settings().log_level)

init_db_with_data()


@mcp.tool()
def create_task(
    title: str,
    priority: Priority,
    complexity: Complexity,
    status: Status = "todo",
    description: str | None = None,
    parent_id: str | None = None,
) -> Task:
    """Create a new task"""
    task_create = TaskCreate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        complexity=complexity,
        parent_id=parent_id,
    )
    return db_create_task(task_create)


@mcp.tool()
def get_task(task_id: str) -> Task | None:
    """Get a task by ID"""
    return db_get_task(task_id)


@mcp.tool()
def list_tasks(
    statuses: list[Status] | None = None, parent_id: str | None = None
) -> list[Task]:
    """List all tasks, optionally filtered by statuses or parent_id. Defaults to ['todo', 'inprogress'] if no statuses provided."""
    return db_list_tasks(statuses, parent_id)


@mcp.tool()
def update_task(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    status: Status | None = None,
    priority: Priority | None = None,
    complexity: Complexity | None = None,
    parent_id: str | None = None,
) -> Task | None:
    """Update a task by ID"""
    task_update = TaskUpdate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        complexity=complexity,
        parent_id=parent_id,
    )
    return db_update_task(task_id, task_update)


@mcp.tool()
def delete_task(task_id: str) -> Task | None:
    """Delete a task by ID"""
    return db_delete_task(task_id)


def run_mcp():
    """Run the TaskHelper MCP server"""
    logger.info("Starting taskhelper MCP server..")
    mcp.run(transport=get_settings().transport)


if __name__ == "__main__":
    run_mcp()
