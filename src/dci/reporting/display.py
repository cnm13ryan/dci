"""Notebook `display` shim: rich in IPython, compact text elsewhere."""
from __future__ import annotations


def display(obj) -> None:
    try:  # pragma: no cover
        from IPython.display import display as _display
        import IPython
        if IPython.get_ipython() is not None:
            _display(obj)
            return
    except Exception:
        pass
    try:
        import pandas as pd
        if isinstance(obj, (pd.DataFrame, pd.Series)) and len(obj) > 30:
            print(obj.head(30).to_string())
            print(f"... [{len(obj)} rows]")
            return
    except Exception:
        pass
    print(obj)
