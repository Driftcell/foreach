foreach MCP Tool
================

An MCP server for batch-processing code files. It keeps a visible task queue so the model can claim files in batches, process, and report results without missing anything.

Features
- Scan directories with smart ignores: honors .gitignore-style patterns and common noisy paths (node_modules, .env, .venv, __pycache__, etc.)
- Task-first workflow: create task → claim next files → done/skip → status → cancel
- Easy start via uv/uvx; works with Claude Desktop and MCP Inspector

Quick start
- Local dev (recommended)
	- Run the server module directly:
		```bash
		uv run python -m foreach.server
		```

- Run as a tool with uvx
	- From Git (no local clone needed):
		```bash
		uvx --from git+https://github.com/driftcell/foreach foreach
		```
	- From a local path (editable dev checkout):
		```bash
		uvx --from /path/to/foreach foreach
		```

MCP tools
- foreach_create_task(root_path, description, include_globs?, exclude_globs?, preview=10)
- foreach_next(task_id, n=1)
- foreach_done(task_id, files: list[str], next_n=1)
- foreach_skip(task_id, files: list[str])
- foreach_status(task_id, list_statuses?: list[str], limit=50, offset=0)
- foreach_cancel(task_id)

Example Usage
User:

		/foreach Somedir Please translate all Chinese in these code files into English, and expand all abbreviations to their full forms.

Flow (tool-call sequence for the model):
1) Call foreach_create_task:
	 - root_path: Somedir
	 - description: "Translate all Chinese in these code files to English, then expand all abbreviations to full names"
2) Loop:
	 - Call foreach_next to claim N files
	 - Model edits those files
	 - Call foreach_done(files=[...]) to report completion, or foreach_skip(files=[...]) to skip
	 - Call foreach_status anytime to view progress
3) When finished, call foreach_cancel to stop the task

Development Notes
- Code layout:
	- foreach/scanner.py: directory scan + ignore rules
	- foreach/task_manager.py: task and file-queue management
	- foreach/server.py: FastMCP server and tools
	- main.py: entrypoint (calls server.main)

