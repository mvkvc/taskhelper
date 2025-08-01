import argparse
import os
from typing import Optional

_settings: Optional["Settings"] = None


class Settings:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--root", default=os.getcwd())
        parser.add_argument("--db-path", default=".tasks.db")
        parser.add_argument("--tasks-path", default=".tasks")
        parser.add_argument("--transport", default="stdio")
        parser.add_argument(
            "--log-level",
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        )

        args, _ = parser.parse_known_args()

        self.root = args.root
        self.db_path = args.db_path
        self.tasks_path = args.tasks_path
        self.transport = args.transport
        self.log_level = args.log_level


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
