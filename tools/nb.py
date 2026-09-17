#!/usr/bin/env python
"""依 cell 標籤操作 .ipynb。

標籤格式：code cell 第一行 `# [cNN] name`；SQL magic cell 第二行 `-- [cNN] name`。

用法：
  python tools/nb.py list   <nb>
  python tools/nb.py show   <nb> <tag>
  python tools/nb.py set    <nb> <tag> <file|->
  python tools/nb.py insert <nb> <after_tag> <file|-> [--markdown]
  python tools/nb.py delete <nb> <tag>
  python tools/nb.py strip  <nb>
  python tools/nb.py export <nb> <tag> [<tag>...]
只依賴標準函式庫。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"^\s*(?:#|--|//)\s*\[(c\d+[a-z]?)\]\s*(\S*)")
MAGIC_RE = re.compile(r"^\s*%")


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path: str, nb: dict) -> None:
    Path(path).write_text(
        json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )


def source_of(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def set_source(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def tag_of(cell: dict) -> tuple[str | None, str]:
    """回傳 (tag, name)。只看前兩行，允許第一行是 %magic。"""
    if cell.get("cell_type") != "code":
        return None, ""
    for line in source_of(cell).splitlines()[:2]:
        m = TAG_RE.match(line)
        if m:
            return m.group(1), m.group(2)
    return None, ""


def find(nb: dict, tag: str) -> int:
    hits = [i for i, c in enumerate(nb["cells"]) if tag_of(c)[0] == tag]
    if not hits:
        sys.exit(f"找不到標籤 [{tag}]")
    if len(hits) > 1:
        sys.exit(f"標籤 [{tag}] 重複出現於 cell {hits}")
    return hits[0]


def read_input(arg: str) -> str:
    return sys.stdin.read() if arg == "-" else Path(arg).read_text(encoding="utf-8")


def new_cell(text: str, markdown: bool = False) -> dict:
    cell: dict = {"cell_type": "markdown" if markdown else "code", "metadata": {}, "source": []}
    if not markdown:
        cell["outputs"] = []
        cell["execution_count"] = None
    set_source(cell, text)
    return cell


def check_tag_in_text(text: str, expect: str | None = None) -> str:
    tag, _ = tag_of(new_cell(text))
    if tag is None:
        sys.exit("新內容第一行（或 %magic 後第二行）必須是標籤，例如 `# [c05] name`")
    if expect and tag != expect:
        sys.exit(f"新內容標籤為 [{tag}]，與目標 [{expect}] 不符")
    return tag


# ---------- commands ----------


def cmd_list(nb: dict) -> None:
    print(f"{'idx':>3}  {'type':<8} {'tag':<6} {'lines':>5}  first line")
    for i, c in enumerate(nb["cells"]):
        lines = source_of(c).splitlines()
        tag, _ = tag_of(c)
        first = lines[0] if lines else ""
        if MAGIC_RE.match(first) and len(lines) > 1:
            first = f"{first.strip()} | {lines[1]}"
        print(f"{i:>3}  {c['cell_type']:<8} {(tag or '-'):<6} {len(lines):>5}  {first[:80]}")


def cmd_show(nb: dict, tag: str) -> None:
    print(source_of(nb["cells"][find(nb, tag)]), end="")


def cmd_set(nb: dict, tag: str, text: str) -> None:
    idx = find(nb, tag)
    check_tag_in_text(text, expect=tag)
    cell = nb["cells"][idx]
    set_source(cell, text)
    cell["outputs"] = []
    cell["execution_count"] = None
    print(f"已替換 [{tag}]（cell {idx}）")


def cmd_insert(nb: dict, after: str, text: str, markdown: bool) -> None:
    idx = find(nb, after)
    if not markdown:
        tag = check_tag_in_text(text)
        if any(tag_of(c)[0] == tag for c in nb["cells"]):
            sys.exit(f"標籤 [{tag}] 已存在")
    nb["cells"].insert(idx + 1, new_cell(text, markdown))
    print(f"已在 [{after}]（cell {idx}）之後插入 cell {idx + 1}")


def cmd_delete(nb: dict, tag: str) -> None:
    idx = find(nb, tag)
    del nb["cells"][idx]
    print(f"已刪除 [{tag}]（cell {idx}）")


def cmd_strip(nb: dict) -> int:
    n = 0
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            if c.get("outputs") or c.get("execution_count") is not None:
                n += 1
            c["outputs"] = []
            c["execution_count"] = None
    return n


def cmd_export(nb: dict, tags: list[str]) -> None:
    for tag in tags:
        src = source_of(nb["cells"][find(nb, tag)])
        lines = [ln for ln in src.splitlines() if not MAGIC_RE.match(ln)]
        print("\n".join(lines).rstrip() + "\n")


def _utf8_stdio() -> None:
    """Windows 主控台預設 cp1252，中文會 UnicodeEncodeError；統一改成 UTF-8。"""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: list[str]) -> None:
    _utf8_stdio()
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd, path, rest = argv[0], argv[1], argv[2:]
    nb = load(path)
    if cmd == "list":
        cmd_list(nb)
    elif cmd == "show":
        cmd_show(nb, rest[0])
    elif cmd == "set":
        cmd_set(nb, rest[0], read_input(rest[1]))
        save(path, nb)
    elif cmd == "insert":
        md = "--markdown" in rest
        rest = [r for r in rest if r != "--markdown"]
        cmd_insert(nb, rest[0], read_input(rest[1]), md)
        save(path, nb)
    elif cmd == "delete":
        cmd_delete(nb, rest[0])
        save(path, nb)
    elif cmd == "strip":
        n = cmd_strip(nb)
        save(path, nb)
        print(f"已清除 {n} 個 cell 的 outputs")
    elif cmd == "export":
        cmd_export(nb, rest)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
