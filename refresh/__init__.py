"""An independently maintained homage to Which Way Is Up?"""
from pathlib import Path
import tomllib

# The source and Arch packages both ship project metadata beside refresh/.
with (Path(__file__).resolve().parents[1] / 'pyproject.toml').open('rb') as _metadata:
    __version__ = tomllib.load(_metadata)['project']['version']
