"""Load the example's native, addressed ZTES specifications."""

from pathlib import Path

from ztes.system.system import System


def system():
    return System(Path(__file__).resolve().parent / "native")
