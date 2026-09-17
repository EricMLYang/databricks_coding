"""依標籤把 .ipynb 內的 code cell 載入成 Python module，供 pytest 使用。

    mod = load_cells("jobs/my_job/notebook.ipynb", ["c02", "c05"])
    mod.transform_orders(df)

限制：被載入的 cell 只能含 def / import / 常數，不可有 spark 讀寫、dbutils、%magic。
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import nb as nbtool  # noqa: E402


def load_cells(notebook: str, tags: list[str], name: str = "nbmod") -> types.ModuleType:
    path = Path(notebook) if Path(notebook).is_absolute() else ROOT / notebook
    nb = nbtool.load(str(path))
    parts = []
    for tag in tags:
        src = nbtool.source_of(nb["cells"][nbtool.find(nb, tag)])
        parts.append("\n".join(ln for ln in src.splitlines() if not nbtool.MAGIC_RE.match(ln)))
    code = "\n\n".join(parts)
    mod = types.ModuleType(name)
    mod.__file__ = f"{path}::{','.join(tags)}"
    exec(compile(code, mod.__file__, "exec"), mod.__dict__)
    return mod
