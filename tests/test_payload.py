"""Tests for IPython.core.payload and IPython.core.payloadpage."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest

from IPython.core import payloadpage
from IPython.core.payload import PayloadManager

# -----------------------------------------------------------------------------
# PayloadManager
# -----------------------------------------------------------------------------


def test_write_payload_requires_dict():
    pm = PayloadManager()
    with pytest.raises(TypeError, match="must be a dict"):
        pm.write_payload("not a dict")


def test_write_and_read_payload():
    pm = PayloadManager()
    assert pm.read_payload() == []
    data = {"source": "page", "text": "hello"}
    pm.write_payload(data)
    assert pm.read_payload() == [data]


def test_write_payload_single_replaces_same_source():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "first"})
    pm.write_payload({"source": "page", "text": "second"})
    assert pm.read_payload() == [{"source": "page", "text": "second"}]


def test_write_payload_single_keeps_other_sources():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "a"})
    pm.write_payload({"source": "edit", "text": "b"})
    pm.write_payload({"source": "page", "text": "c"})
    assert pm.read_payload() == [
        {"source": "page", "text": "c"},
        {"source": "edit", "text": "b"},
    ]


def test_write_payload_not_single_appends():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "a"})
    pm.write_payload({"source": "page", "text": "b"}, single=False)
    assert pm.read_payload() == [
        {"source": "page", "text": "a"},
        {"source": "page", "text": "b"},
    ]


def test_write_payload_without_source_appends():
    pm = PayloadManager()
    pm.write_payload({"text": "a"})
    pm.write_payload({"text": "b"})
    assert pm.read_payload() == [{"text": "a"}, {"text": "b"}]


def test_clear_payload():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "a"})
    pm.clear_payload()
    assert pm.read_payload() == []


# -----------------------------------------------------------------------------
# payloadpage.page
# -----------------------------------------------------------------------------


class FakeShell:
    def __init__(self):
        self.payload_manager = PayloadManager()


@pytest.fixture
def fake_shell(monkeypatch):
    shell = FakeShell()
    monkeypatch.setattr(payloadpage, "get_ipython", lambda: shell)
    return shell


def test_payloadpage_string(fake_shell):
    payloadpage.page("some text", start=3)
    assert fake_shell.payload_manager.read_payload() == [
        {"source": "page", "data": {"text/plain": "some text"}, "start": 3}
    ]


def test_payloadpage_mime_bundle(fake_shell):
    bundle = {"text/plain": "plain", "text/html": "<b>html</b>"}
    payloadpage.page(bundle)
    assert fake_shell.payload_manager.read_payload() == [
        {"source": "page", "data": bundle, "start": 0}
    ]


def test_payloadpage_negative_start_clamped(fake_shell):
    payloadpage.page("text", start=-10)
    (payload,) = fake_shell.payload_manager.read_payload()
    assert payload["start"] == 0


def test_payloadpage_single_payload_overwritten(fake_shell):
    # both writes share source="page", so only the last one is kept
    payloadpage.page("first")
    payloadpage.page("second")
    (payload,) = fake_shell.payload_manager.read_payload()
    assert payload["data"] == {"text/plain": "second"}
