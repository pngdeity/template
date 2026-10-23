#!/usr/bin/env python3
"""Drop the deprecated `static/` directory from a project generated before v1.1.0."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".")
    static = root / "static"
    if not static.is_dir():
        print(f"{static} does not exist; nothing to migrate.")
        return 0
    if any(static.iterdir()):
        print(
            f"{static} is not empty. Move what you need out of it, then rerun.",
            file=sys.stderr,
        )
        return 1
    shutil.rmtree(static)
    print(f"Removed {static}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
