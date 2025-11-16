
"""
notebook_scribe.py
-------------------
Skryba do Jupyter Notebook, który potrafi:
- generować funkcje/formuły/snippety do nowej komórki,
- **wypisywać kod literka po literce** (efekt "typewriter") w klasycznym Jupyter Notebook.

Uwaga: tryb "typewriter" wymaga klasycznego Jupytera (interfejs z CodeMirror, zmienna `Jupyter` w JS).
W JupyterLab większość API frontendu jest niedostępna — wtedy zostanie użyty bezpieczny fallback
(komórka z pełnym kodem bez animacji).
"""

from __future__ import annotations
from textwrap import dedent

# --- niskopoziomowe narzędzia ---
try:
    from IPython import get_ipython
    from IPython.display import Javascript, display
except Exception:  # gdy poza IPython
    get_ipython = lambda: None
    Javascript = None
    def display(*args, **kwargs):  # no-op
        print(*args)

def _ensure_next_cell(code: str, execute: bool = False) -> None:
    """Wstaw kod do następnej komórki (bez animacji)."""
    ip = get_ipython()
    if ip is None:
        print(code)
        return
    code = dedent(code).rstrip() + "\n"
    ip.set_next_input(code, replace=False)
    if execute:
        ip.run_cell(code)

def _indent(body: str, spaces: int = 4) -> str:
    body = dedent(body).rstrip("\n")
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else "" for line in body.splitlines())

def _pep8_function_header(name: str, args) -> str:
    args_str = ", ".join(args)
    return f"def {name}({args_str}):"

# --- główna klasa ---
class NotebookScribe:
    """Generator kodu + animowane pisanie (classic Jupyter)."""

    # Typing / typewriter
    def typewriter(self, code: str, delay_ms: int = 20, new_cell: bool = True, execute_after: bool = False):
        """
        Wypisuje `code` znak po znaku w komórce kodowej (classic Jupyter).
        - delay_ms: opóźnienie między znakami (ms)
        - new_cell: True -> utwórz nową komórkę pod bieżącą; False -> użyj bieżącej
        - execute_after: True -> po zakończeniu animacji uruchom tę komórkę

        Fallback (JupyterLab/VS Code): wstawi cały kod bez animacji.
        """
        ip = get_ipython()
        js_env_ok = (Javascript is not None and ip is not None)

        if not js_env_ok:
            return _ensure_next_cell(code, execute=False)

        # Spróbuj wykonać animację po stronie przeglądarki (classic Jupyter)
        js = f"""
(function() {{
    var txt = {code!r};
    var delay = {int(delay_ms)};

    function classicNotebookAvailable() {{
        return (typeof Jupyter !== "undefined") && Jupyter.notebook && Jupyter.notebook.insert_cell_below;
    }}

    if (!classicNotebookAvailable()) {{
        // Brak klasycznego frontendu -> fallback (bez animacji)
        return;
    }}

    var cell = null;
    if ({str(bool(new_cell)).lower()}) {{
        cell = Jupyter.notebook.insert_cell_below('code');
        Jupyter.notebook.select_next();
        Jupyter.notebook.scroll_to_cell(Jupyter.notebook.get_selected_index());
    }} else {{
        cell = Jupyter.notebook.get_selected_cell();
        if (!cell) {{
            cell = Jupyter.notebook.insert_cell_below('code');
            Jupyter.notebook.select_next();
        }}
    }}

    var cm = cell && cell.code_mirror;
    if (!cm) {{ return; }}

    cm.setValue('');  // zacznij od pustej komórki

    var i = 0;
    function typeNext() {{
        if (i >= txt.length) {{
            cm.refresh();
            cm.execCommand('goDocEnd');
            { "Jupyter.notebook.execute_cell();" if execute_after else "" }
            return;
        }}
        var ch = txt.charAt(i);
        var doc = cm.getDoc();
        var endPos = doc.posFromIndex(doc.getValue().length);
        doc.replaceRange(ch, endPos);
        cm.execCommand('goDocEnd');  // auto-scroll
        i++;
        setTimeout(typeNext, delay);
    }}
    typeNext();
}})();
"""
        try:
            display(Javascript(js))
        except Exception:
            # Fallback gdy frontend odrzuci JS
            _ensure_next_cell(code, execute=False)

    # Generatory kodu (bez animacji, ale można użyć razem z typewriter)
    def function(self, name, args=(), doc=None, body="pass", insert_cell=True, execute=False):
        header = _pep8_function_header(name, args)
        ds = f'    """{doc}"""\n' if doc else ""
        body_ind = _indent(body, 4)
        code = f"""{header}
{ds}{body_ind}
"""
        if insert_cell:
            _ensure_next_cell(code, execute)
        return code

    def formula(self, expression: str, insert_cell=True, execute=False) -> str:
        expr = expression.replace("^", "**")
        code = expr
        if insert_cell:
            _ensure_next_cell(code, execute)
        return code

    def snippet(self, name: str, insert_cell=True, execute=False, **kwargs) -> str:
        if name == "read_csv":
            path = kwargs.get("path", "data.csv")
            code = f"import pandas as pd\ndf = pd.read_csv({path!r})\ndf.head()"
        else:
            raise ValueError(f"Nieznany snippet: {name}")
        if insert_cell:
            _ensure_next_cell(code, execute)
        return code

# Obiekt do użycia
scribe = NotebookScribe()
