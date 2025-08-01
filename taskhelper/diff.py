# https://github.com/simonw/sqlite-diffable/blob/dfe290c982bfc5a94bb1df199badde5a931606a1/sqlite_diffable/cli.py

# type: ignore

import json
import pathlib
import sqlite_utils
import sqlite3
from typing import List, Optional, Union


def dump_database(
    dbpath: Union[str, pathlib.Path],
    output_dir: Union[str, pathlib.Path],
    tables: Optional[List[str]] = None,
    dump_all: bool = False,
    exclude: Optional[List[str]] = None,
) -> None:
    """
    Dump a SQLite database out as flat files in the directory.

    Args:
        dbpath: Path to the SQLite database file
        output_dir: Directory to dump files to
        tables: List of specific tables to dump
        dump_all: If True, dump all tables
        exclude: List of tables to exclude from the dump

    Raises:
        ValueError: If neither tables nor dump_all is specified
    """
    if not tables and not dump_all:
        raise ValueError("You must specify dump_all=True or provide a list of tables")

    exclude = exclude or []
    output = pathlib.Path(output_dir)
    output.mkdir(exist_ok=True)

    conn = sqlite_utils.Database(dbpath)

    if dump_all:
        tables_to_dump = set(conn.table_names()) - set(exclude)
    else:
        tables_to_dump = set(tables) - set(exclude)

    for table in tables_to_dump:
        tablename = table.replace("/", "")
        filepath = output / f"{tablename}.ndjson"
        metapath = output / f"{tablename}.metadata.json"

        with filepath.open("w") as fp:
            for row in conn[table].rows:
                fp.write(json.dumps(list(row.values()), default=repr) + "\n")

        metadata = {
            "name": table,
            "columns": [c.name for c in conn[table].columns],
            "schema": conn[table].schema,
        }

        with metapath.open("w") as fp:
            fp.write(json.dumps(metadata, indent=4))


def load_database(
    dbpath: Union[str, pathlib.Path],
    directory: Union[str, pathlib.Path],
    replace: bool = False,
) -> None:
    """
    Load flat files from a directory into a SQLite database.

    Args:
        dbpath: Path to the SQLite database file
        directory: Directory containing the dump files
        replace: If True, replace tables if they exist already

    Raises:
        sqlite3.OperationalError: If table already exists and replace=False
    """
    db = sqlite_utils.Database(dbpath)
    directory = pathlib.Path(directory)
    metadatas = directory.glob("*.metadata.json")

    for metadata in metadatas:
        info = json.loads(metadata.read_text())
        columns = info["columns"]
        schema = info["schema"]

        if db[info["name"]].exists() and replace:
            db[info["name"]].drop()

        try:
            db.execute(schema)
        except sqlite3.OperationalError as ex:
            msg = str(ex)
            if "already exists" in msg:
                msg += "\n\nUse replace=True to over-write existing tables"
            raise sqlite3.OperationalError(msg)

        ndjson = metadata.parent / metadata.stem.replace(".metadata", ".ndjson")
        rows = (
            dict(zip(columns, json.loads(line)))
            for line in ndjson.open()
            if line.strip()
        )
        db[info["name"]].insert_all(rows)
