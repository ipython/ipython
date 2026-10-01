"""
Docstring and signature popup for terminal IPython.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from typing import Any

from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition, has_focus, is_done, has_completions
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension


def find_float_container(container: Any) -> FloatContainer | None:
    """Recursively search for the primary FloatContainer in a container hierarchy."""
    if isinstance(container, FloatContainer):
        return container
    for child in getattr(container, "children", []):
        res = find_float_container(child)
        if res is not None:
            return res
    for child in [
        getattr(container, "content", None),
        getattr(container, "alternative_content", None),
    ]:
        if child is not None:
            res = find_float_container(child)
            if res is not None:
                return res
    return None


def get_doc_info(
    text: str,
    cursor_position: int,
    namespaces: list[dict[str, Any]] | None = None,
    shell: Any = None,
) -> dict[str, Any] | None:
    """
    Retrieve signature and docstring for the call at cursor_position.
    Uses Jedi first, then falls back to IPython's shell._ofind / inspect.
    """
    text_before_cursor = text[:cursor_position]
    # Fast check: must have at least one unclosed parenthesis
    if text_before_cursor.count("(") <= text_before_cursor.count(")"):
        return None

    # Check if the unclosed '(' is part of a function or class definition
    idx = text_before_cursor.rfind("(")
    if idx != -1:
        prefix = text_before_cursor[:idx].strip()
        if re.search(r"\b(def|class|async\s+def)\s+[a-zA-Z_][a-zA-Z0-9_]*$", prefix):
            return None

    namespaces = namespaces or []

    # 1. Try Jedi
    try:
        import jedi

        lines = text_before_cursor.split("\n")
        line = len(lines)
        column = len(lines[-1])

        interp = jedi.Interpreter(text_before_cursor, namespaces)
        signatures = interp.get_signatures(line=line, column=column)
        if signatures:
            sig = signatures[0]
            sig_text = sig.to_string()
            doc_text = sig.docstring() or ""
            # Strip redundant signature repetition from docstring if present
            doc_lines = doc_text.strip().splitlines()
            if doc_lines and doc_lines[0].strip() == sig_text.strip():
                doc_lines = doc_lines[1:]
            while doc_lines and not doc_lines[0].strip():
                doc_lines = doc_lines[1:]
            clean_doc = "\n".join(doc_lines)
            return {
                "name": sig.name,
                "signature": sig_text,
                "docstring": clean_doc,
                "params": [p.name for p in sig.params if p is not None],
                "index": sig.index,
            }
    except Exception:
        pass

    # 2. Fallback: shell._ofind and inspect.signature / inspect.getdoc
    if shell is not None:
        try:
            open_idx = text_before_cursor.rfind("(")
            if open_idx > 0:
                prefix = text_before_cursor[:open_idx].rstrip()
                m = re.search(r"([a-zA-Z_][a-zA-Z0-9_\.]*)$", prefix)
                if m:
                    name = m.group(1)
                    info = shell._ofind(name)
                    if info.found and callable(info.obj):
                        try:
                            sig_obj = inspect.signature(info.obj)
                            sig_text = f"{name}{sig_obj}"
                        except Exception:
                            sig_text = f"{name}(...)"
                        doc = inspect.getdoc(info.obj) or ""
                        return {
                            "name": name,
                            "signature": sig_text,
                            "docstring": doc,
                            "params": [],
                            "index": None,
                        }
        except Exception:
            pass

    return None


class DocstringTooltip:
    """
    Manages the function signature and docstring popup in prompt-toolkit.
    """

    def __init__(
        self,
        shell: Any,
        delay: float = 0.2,
        max_lines: int = 12,
        max_width: int = 80,
    ) -> None:
        self.shell = shell
        self.delay = delay
        self.max_lines = max_lines
        self.max_width = max_width
        self.doc_info: dict[str, Any] | None = None
        self._pending_task: asyncio.Task[None] | None = None
        self._request_id: int = 0
        self._connected = False
        self._app: Any = None

    @property
    def visible(self) -> bool:
        return self.doc_info is not None

    def connect(self, pt_app: Any) -> None:
        """Attach the tooltip float and event listeners to PromptSession."""
        self._app = pt_app
        fc = find_float_container(pt_app.layout.container)
        if fc is not None:
            fl = Float(
                content=ConditionalContainer(
                    content=Window(
                        content=FormattedTextControl(self._get_formatted_text),
                        dont_extend_width=True,
                        dont_extend_height=True,
                        wrap_lines=True,
                        width=Dimension(min=1, max=self.max_width),
                        height=Dimension(min=1, max=self.max_lines + 2),
                        style="class:completion-menu",
                    ),
                    filter=Condition(lambda: self.visible)
                    & has_focus(DEFAULT_BUFFER)
                    & ~is_done
                    & ~has_completions,
                ),
                xcursor=True,
                ycursor=True,
                allow_cover_cursor=False,
                z_index=10**7,
            )
            fc.floats.append(fl)
            pt_app.default_buffer.on_text_changed += self._on_text_changed
            pt_app.default_buffer.on_cursor_position_changed += (
                self._on_cursor_position_changed
            )
            self._connected = True

    def _get_formatted_text(self) -> StyleAndTextTuples:
        if not self.doc_info:
            return []
        sig = self.doc_info.get("signature") or ""
        doc = self.doc_info.get("docstring") or ""
        fragments: StyleAndTextTuples = []
        if sig:
            fragments.append(
                ("class:completion-menu.completion.current bold", f" {sig} \n")
            )
        if doc:
            doc_lines = doc.splitlines()
            if len(doc_lines) > self.max_lines:
                doc_lines = doc_lines[: self.max_lines] + ["..."]
            for line in doc_lines:
                fragments.append(("class:completion-menu.meta", f" {line}\n"))
        return fragments

    def _on_text_changed(self, buffer: Buffer) -> None:
        text_before_cursor = buffer.document.text_before_cursor
        if text_before_cursor.count("(") <= text_before_cursor.count(")"):
            self.clear()
            return
        self._schedule_lookup(buffer)

    def _on_cursor_position_changed(self, buffer: Buffer) -> None:
        text_before_cursor = buffer.document.text_before_cursor
        if text_before_cursor.count("(") <= text_before_cursor.count(")"):
            self.clear()
            return
        self._schedule_lookup(buffer)

    def _schedule_lookup(self, buffer: Buffer) -> None:
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()
            self._pending_task = None

        self._request_id += 1
        req_id = self._request_id

        try:
            app = get_app()
        except Exception:
            app = None

        if app is not None and getattr(app, "is_running", False):
            self._pending_task = app.create_background_task(
                self._debounced_lookup(buffer, req_id)
            )

    async def _debounced_lookup(self, buffer: Buffer, req_id: int) -> None:
        try:
            if self.delay > 0:
                await asyncio.sleep(self.delay)

            if req_id != self._request_id:
                return

            doc = buffer.document
            loop = asyncio.get_running_loop()
            namespaces = (
                [self.shell.user_ns, self.shell.user_global_ns] if self.shell else []
            )

            doc_info = await loop.run_in_executor(
                None,
                get_doc_info,
                doc.text,
                doc.cursor_position,
                namespaces,
                self.shell,
            )

            # Check that the request is still current and the buffer has not changed during lookup
            if (
                req_id == self._request_id
                and buffer.document.text == doc.text
                and buffer.document.cursor_position == doc.cursor_position
            ):
                self.doc_info = doc_info
                try:
                    app = get_app()
                    app.invalidate()
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def clear(self) -> None:
        """Reset docstring tooltip state and cancel any pending lookup."""
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()
            self._pending_task = None
        if self.doc_info is not None:
            self.doc_info = None
            try:
                app = get_app()
                if getattr(app, "is_running", False):
                    app.invalidate()
            except Exception:
                pass
