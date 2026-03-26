"""Entry point for pip-installed `gads` command.

When installed via `pip install .`, running `gads` invokes this module.
For direct execution, use `./gads` (the script in the repo root).
"""
import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path


def main():
    """Load and run the gads CLI script."""
    # The main CLI script is `gads` (no .py extension) in the package root
    script_path = Path(__file__).resolve().parent.parent / "gads"
    if not script_path.exists():
        print(f"ERROR: gads script not found at {script_path}", file=sys.stderr)
        sys.exit(1)

    loader = importlib.machinery.SourceFileLoader("gads_main", str(script_path))
    spec = importlib.util.spec_from_loader("gads_main", loader)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(script_path)
    spec.loader.exec_module(mod)
    mod.cli()


if __name__ == "__main__":
    main()
