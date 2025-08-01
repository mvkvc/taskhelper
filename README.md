# taskhelper

An MCP server and CLI for hierarchical task tracking in software projects. Tasks are stored in SQLite and automatically synchronized to diffable text files for version control using [simonw/sqlite-diffable](https://github.com/simonw/sqlite-diffable).

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation)

## Quickstart

### MCP server

Add this entry to your MCP servers settings file:

```json
{
  "mcpServers": {
    "taskhelper": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mvkvc/taskhelper.git",
        "taskhelper-mcp",
        "--root=."
      ]
    }
  }
}
```

### CLI

Run directly with `uvx`:

```sh
uvx --from git+https://github.com/mvkvc/taskhelper.git taskhelper [command]
```

Or install as a `uv` tool:

```sh
uv tool install --from git+https://github.com/mvkvc/taskhelper.git taskhelper
```

After installation, you can run:

```sh
taskhelper [command]
```
