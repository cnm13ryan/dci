"""Assemble the v15 cell files into a Colab notebook."""
import json
import sys
from pathlib import Path

CELLS = Path(__file__).parent / "cells"
OUT = Path(__file__).parent / "directional_constraint_interference_v15.ipynb"


def build() -> dict:
    cells = []
    for path in sorted(CELLS.iterdir()):
        if path.suffix not in (".md", ".py"):
            continue
        source = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
        source = [line + "\n" for line in source[:-1]] + [source[-1]]
        if path.suffix == ".md":
            cells.append({"cell_type": "markdown", "metadata": {}, "source": source})
        else:
            cells.append({"cell_type": "code", "execution_count": None,
                          "metadata": {}, "outputs": [], "source": source})
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "T4",
                      "name": "directional_constraint_interference_v15.ipynb"},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


if __name__ == "__main__":
    nb = build()
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    n_code = sum(1 for c in nb["cells"] if c["cell_type"] == "code")
    n_md = len(nb["cells"]) - n_code
    chars = sum(len("".join(c["source"])) for c in nb["cells"])
    print(f"wrote {OUT}  ({len(nb['cells'])} cells: {n_code} code, {n_md} markdown, "
          f"{chars:,} chars)")
