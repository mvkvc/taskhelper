from datetime import datetime, timezone
import logging
import os

import alembic.config
import alembic.command
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from .config import get_settings
from .diff import (
    dump_database as diff_dump_database,
    load_database as diff_load_database,
)
from .task import TaskCreate, TaskUpdate, Status
from .task import Task as TaskModel

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)

Base = declarative_base()


class Task(Base):
    """Task model for the database"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    hierarchical_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String)
    priority = Column(String)
    complexity = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    parent_hierarchical_id = Column(
        String, ForeignKey("tasks.hierarchical_id"), nullable=True
    )

    child_tasks = relationship(
        "Task", backref="parent_task", remote_side=[hierarchical_id]
    )


@event.listens_for(Task, "before_insert")
def calculate_hierarchical_id(mapper, connection, target):
    """Automatically calculate hierarchical_id before a task is inserted"""
    from sqlalchemy import text

    if target.parent_hierarchical_id is None:
        count_result = connection.execute(
            text("SELECT COUNT(*) FROM tasks WHERE parent_hierarchical_id IS NULL")
        ).fetchone()
        target.hierarchical_id = str(count_result[0] + 1)
    else:
        parent_id = target.parent_hierarchical_id

        sibling_count_result = connection.execute(
            text(
                "SELECT COUNT(*) FROM tasks WHERE parent_hierarchical_id = :parent_id"
            ),
            {"parent_id": target.parent_hierarchical_id},
        ).fetchone()
        sibling_position = sibling_count_result[0] + 1

        target.hierarchical_id = f"{parent_id}.{sibling_position}"


engine = None
SessionLocal: sessionmaker[Session] | None = None


def init_db_engine():
    """Initialize the database engine with configured path"""
    global engine, SessionLocal
    settings = get_settings()
    db_path = os.path.join(settings.root, settings.db_path)
    db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
    os.makedirs(db_dir, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database and create tables"""
    if engine is None:
        init_db_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    if SessionLocal is None:
        init_db_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def create_task(task_create: TaskCreate) -> TaskModel:
    """Create a new task in the database using Pydantic model and return the created Task"""
    db = get_db()
    try:
        task = Task(
            title=task_create.title,
            description=task_create.description,
            status=task_create.status,
            priority=task_create.priority,
            complexity=task_create.complexity,
            parent_hierarchical_id=task_create.parent_id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        dump_database()

        return TaskModel.from_db(task)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_task(task_id: str) -> TaskModel | None:
    """Get a task by ID and return as Pydantic model"""
    db = get_db()
    try:
        task = db.query(Task).filter(Task.hierarchical_id == task_id).first()
        if task:
            return TaskModel.from_db(task)
        else:
            return None
    finally:
        db.close()


def list_tasks(
    statuses: list[Status] | None = None, parent_id: str | None = None
) -> list[TaskModel]:
    """List all tasks, optionally filtered by statuses or parent_id, ordered hierarchically"""
    if statuses is None:
        statuses = ["todo", "inprogress"]

    db = get_db()
    try:
        query = db.query(Task)
        if statuses:
            query = query.filter(Task.status.in_(statuses))
        if parent_id is not None:
            query = query.filter(Task.parent_hierarchical_id == parent_id)

        tasks = query.all()

        task_models = [TaskModel.from_db(task) for task in tasks]

        def hierarchical_key(task):
            return [int(x) for x in task.id.split(".")]

        task_models.sort(key=hierarchical_key)

        return task_models
    finally:
        db.close()


def update_task(task_id: str, task_update: TaskUpdate) -> TaskModel | None:
    """Update a task by ID using Pydantic model and return the updated Task"""
    db = get_db()
    try:
        task = db.query(Task).filter(Task.hierarchical_id == task_id).first()
        if not task:
            return None

        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = task_update.status
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.complexity is not None:
            task.complexity = task_update.complexity
        if task_update.parent_id is not None:
            task.parent_hierarchical_id = task_update.parent_id

        task.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(task)
        dump_database()

        return TaskModel.from_db(task)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_task(task_id: str) -> TaskModel | None:
    """Delete a task by ID and return the deleted task"""
    db = get_db()
    try:
        task = db.query(Task).filter(Task.hierarchical_id == task_id).first()
        if not task:
            return None

        deleted_task = TaskModel.from_db(task)

        db.delete(task)
        db.commit()
        dump_database()
        return deleted_task
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def load_database():
    """Load database from diffable files"""
    settings = get_settings()
    tasks_folder = os.path.join(settings.root, settings.tasks_path)
    db_path = os.path.join(settings.root, settings.db_path)

    if os.path.exists(tasks_folder):
        logger.debug(f"Loading database from diffable files: {tasks_folder}")
        diff_load_database(db_path, tasks_folder, replace=True)
        logger.debug("Database loaded successfully")


def dump_database():
    """Dump database to diffable files"""
    settings = get_settings()
    tasks_folder = os.path.join(settings.root, settings.tasks_path)
    db_path = os.path.join(settings.root, settings.db_path)

    logger.debug(f"Dumping database to diffable files: {tasks_folder}")
    diff_dump_database(db_path, tasks_folder, dump_all=True)
    logger.debug("Database dumped successfully")


def apply_migrations():
    """Apply Alembic migrations automatically"""
    taskhelper_dir_path = os.path.dirname(os.path.abspath(__file__))
    alembic_dir_path = os.path.join(taskhelper_dir_path, "alembic")
    alembic_ini_path = os.path.join(alembic_dir_path, "alembic.ini")

    config = alembic.config.Config(alembic_ini_path)
    config.set_main_option("script_location", alembic_dir_path)

    alembic.command.upgrade(config, "head")
    logger.debug("Database migrations applied successfully")
    return True


def init_db_with_data():
    """Initialize the database and load from files if they exist"""
    init_db()
    apply_migrations()
    load_database()
