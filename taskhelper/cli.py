import click
from typing import Optional, List
from tabulate import tabulate

from .db import (
    init_db_with_data,
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
)
from .task import Task, TaskCreate, TaskUpdate, Status, Priority, Complexity


def display_tasks_table(tasks: List[Task]):
    headers = [
        "ID",
        "Title",
        "Description",
        "Status",
        "Priority",
        "Complexity",
    ]
    table_data = []
    for task in tasks:
        table_data.append(
            [
                task.id,
                task.title,
                task.description if task.description else "",
                task.status,
                task.priority,
                task.complexity,
            ]
        )

    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@click.group()
def cli():
    """taskhelper-cli - Manage tasks from the command line"""
    pass


@cli.command()
@click.option("--title", "-t", required=True, help="Task title")
@click.option("--description", "-d", help="Task description")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["todo", "inprogress", "done"]),
    default="todo",
    help="Task status",
)
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["low", "medium", "high"]),
    required=True,
    help="Task priority",
)
@click.option(
    "--complexity",
    "-c",
    type=click.Choice(["low", "medium", "high"]),
    required=True,
    help="Task complexity",
)
@click.option("--parent-id", "-P", type=str, help="Parent task ID")
def create(
    title: str,
    description: Optional[str],
    status: Status,
    priority: Priority,
    complexity: Complexity,
    parent_id: Optional[str],
):
    """Create a new task"""
    init_db_with_data()

    task_create = TaskCreate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        complexity=complexity,
        parent_id=parent_id,
    )

    try:
        task = create_task(task_create)
        display_tasks_table([task])
    except Exception as e:
        click.echo(f"Error creating task: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--status",
    "-s",
    type=click.Choice(["todo", "inprogress", "done"]),
    multiple=True,
    help="Filter tasks by status (can be used multiple times). Defaults to 'todo' and 'inprogress' if not specified.",
)
@click.option("--parent-id", "-P", type=str, help="Filter tasks by parent ID")
def list(status: tuple[Status, ...], parent_id: Optional[str]):
    """List all tasks"""
    init_db_with_data()

    try:
        statuses = list(status) if status else None
        tasks = list_tasks(statuses=statuses, parent_id=parent_id)
        display_tasks_table(tasks)
    except Exception as e:
        click.echo(f"Error listing tasks: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("task_id", type=str)
def get(task_id: str):
    """Get a task by ID"""
    init_db_with_data()

    task = get_task(task_id)
    if not task:
        click.echo(f"Task {task_id} not found")
        return

    display_tasks_table([task])


@cli.command()
@click.argument("task_id", type=str)
@click.option("--title", "-t", help="New task title")
@click.option("--description", "-d", help="New task description")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["todo", "inprogress", "done"]),
    help="New task status",
)
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["low", "medium", "high"]),
    help="New task priority",
)
@click.option(
    "--complexity",
    "-c",
    type=click.Choice(["low", "medium", "high"]),
    help="New task complexity",
)
@click.option("--parent-id", "-P", type=str, help="New parent task ID")
def update(
    task_id: str,
    title: Optional[str],
    description: Optional[str],
    status: Optional[Status],
    priority: Optional[Priority],
    complexity: Optional[Complexity],
    parent_id: Optional[str],
):
    """Update a task by ID"""
    init_db_with_data()

    existing_task = get_task(task_id)
    if not existing_task:
        click.echo(f"Task {task_id} not found")
        return

    task_update = TaskUpdate(
        title=title,
        description=description,
        status=status,
        priority=priority,
        complexity=complexity,
        parent_id=parent_id,
    )

    updated_task = update_task(task_id, task_update)
    if updated_task:
        display_tasks_table([updated_task])
    else:
        click.echo(f"Failed to update task #{task_id}")


@cli.command()
@click.argument("task_id", type=str)
def delete(task_id: str):
    """Delete a task by ID"""
    init_db_with_data()

    deleted_task = delete_task(task_id)
    if deleted_task:
        display_tasks_table([deleted_task])
    else:
        click.echo(f"Task {task_id} not found")


if __name__ == "__main__":
    cli()
