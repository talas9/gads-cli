"""CLI entry point for pip-installed usage: `gads` command."""
import importlib.machinery
import os

_gads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gads")
_loader = importlib.machinery.SourceFileLoader("_gads_main", _gads_path)
_mod = _loader.load_module()

cli = _mod.cli


def main():
    cli()
