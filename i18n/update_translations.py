""" Scan plugin folder for translations"""

import os
import contextlib

from pathlib import Path

LANGUAGE_LIST = ["en", "fr"]
PLUGIN_NAME = "MultiLayerSelect"


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def get_ts_list():
    """Compute the list of generated ts files"""
    return " ".join(f"./{PLUGIN_NAME}_{language}.ts" for language in LANGUAGE_LIST)


if __name__ == "__main__":
    with working_directory(Path(__file__).parent):
        PATHS = []
        for filepath in Path("..").rglob("*.py"):
            PATHS.append(f'"{filepath}"')
        os.system(
            f"pylupdate5 -verbose -noobsolete {' '.join(PATHS)} -ts {get_ts_list()}"
        )
