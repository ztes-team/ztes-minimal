"""Construct the native system for the published-mask policy or its fresh control."""

from pathlib import Path

from ztes.system.authoring import read_directory
from ztes.system.system import System


def system(fresh=False):
    definition = read_directory(Path(__file__).with_name("native"))
    if fresh:
        definition["constants"]["POLICY"] = "fresh"
    return System.from_dict(definition)
