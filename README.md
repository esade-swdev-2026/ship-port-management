## Who is this for 
This project is for port managers to track the activity in their ports, while making sure incoming movement is valid. 


## Install

```
uv sync
```

This creates a virtual environment and installs everything, including the development
tools, from `uv.lock` — the committed file that pins exact versions so every teammate
and CI resolve the same ones. When you change a dependency in `pyproject.toml`, run
`uv lock` and commit the updated `uv.lock`; CI fails if the two disagree.

## Run

```
uv run ship-port-management --help
uv run ship-port-management register-vessel MV-ATLAS 500 --cargo-units 40
```

## Develop

```
uv run ruff check .          # lint
uv run ruff format .         # format (CI runs `--check` and fails on a diff)
uv run mypy src tests        # types
uv run pytest                # tests
```

These four commands are exactly what `.github/workflows/check.yml` runs on every push.
If they pass here, CI passes.

## Layout

```
src/ship_port_management/   your package — importable, installable, not just a script
  cli.py                    the typer command-line interface
  __main__.py               lets `python -m ship_port_management` work
tests/                      pytest tests, mirroring src/
pyproject.toml              dependencies and tool configuration — the single source of truth
```