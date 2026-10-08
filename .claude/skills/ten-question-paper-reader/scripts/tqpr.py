#!/usr/bin/env python3
"""Self-locating entry point for the ten-question-paper-reader Codex skill.

Why this exists
---------------
The original VS Code extension resolved the Python ``core`` package as
``<extension-install-dir>/../../../core``. Once packaged as a VSIX that path
points inside VS Code's extension host folder, where ``core/`` does not exist,
so the tool only ran when the repo was opened in Extension Development Host.

This launcher instead resolves ``core/`` relative to *its own location*:

  1. Prefer the canonical repo-root ``core/`` (walk up from this script).
  2. Fall back to the bundled copy shipped inside this skill
     (``scripts/bundled/core``), so the skill keeps working even when copied
     standalone to ``~/.codex/skills/`` with no repo around.

It then hands off to ``core.cli:main`` with the original argv untouched.
"""
import os
import sys


def _candidate_core_roots():
    """Yield directories that *contain* the ``core`` package, in priority order."""
    here = os.path.dirname(os.path.abspath(__file__))

    # 1) Repo-root core: here = <repo>/.codex/skills/<skill>/scripts
    #    walk up until we find a directory that itself contains core/config.py
    cursor = here
    for _ in range(6):
        cursor = os.path.dirname(cursor)
        if os.path.isfile(os.path.join(cursor, "core", "config.py")):
            yield cursor

    # 2) Bundled copy next to this script (self-contained skill).
    bundled_parent = os.path.join(here, "bundled")
    if os.path.isfile(os.path.join(bundled_parent, "core", "config.py")):
        yield bundled_parent


def main():
    for root in _candidate_core_roots():
        sys.path.insert(0, root)
        try:
            from core.cli import main as cli_main
        except Exception:
            # This root was unusable; try the next candidate.
            continue
        # Dispatch with the caller's argv (strip this script name).
        sys.argv[0] = os.path.join(root, "core", "cli.py")
        cli_main()
        return

    sys.stderr.write(
        "[tqpr] 找不到 Python 运行时 core/ 包。\n"
        "已按以下顺序查找：\n"
        "  1. 从本脚本向上查找仓库根目录下的 core/\n"
        "  2. skill 自带的 scripts/bundled/core/\n"
        "请确认：\n"
        "  - 你仍在 ten-question-paper-reader 仓库内运行；或\n"
        "  - scripts/bundled/core 副本完整存在。\n"
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
