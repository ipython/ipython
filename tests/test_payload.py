"""Tests for IPython.core.payload."""

import pytest

from IPython.core.payload import PayloadManager


def test_write_payload_stores_dict():
    pm = PayloadManager()
    pm.write_payload({"source": "test", "data": "hello"})
    assert len(pm.read_payload()) == 1


def test_write_payload_non_dict_raises_type_error():
    pm = PayloadManager()
    with pytest.raises(TypeError, match="dict"):
        pm.write_payload("not a dict")


def test_write_payload_list_raises_type_error():
    pm = PayloadManager()
    with pytest.raises(TypeError):
        pm.write_payload(["a", "b"])


def test_write_payload_single_true_updates_same_source():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "first"})
    pm.write_payload({"source": "page", "text": "second"}, single=True)
    payload = pm.read_payload()
    assert len(payload) == 1
    assert payload[0]["text"] == "second"


def test_write_payload_single_false_appends():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "first"})
    pm.write_payload({"source": "page", "text": "second"}, single=False)
    payload = pm.read_payload()
    assert len(payload) == 2


def test_write_payload_no_source_always_appends():
    pm = PayloadManager()
    pm.write_payload({"data": "a"})
    pm.write_payload({"data": "b"})
    assert len(pm.read_payload()) == 2


def test_write_payload_different_sources_both_kept():
    pm = PayloadManager()
    pm.write_payload({"source": "page", "text": "page content"})
    pm.write_payload({"source": "edit", "text": "edit content"})
    assert len(pm.read_payload()) == 2


def test_read_payload_returns_all():
    pm = PayloadManager()
    pm.write_payload({"source": "a"})
    pm.write_payload({"source": "b"})
    result = pm.read_payload()
    sources = [p["source"] for p in result]
    assert "a" in sources
    assert "b" in sources


def test_clear_payload_empties_list():
    pm = PayloadManager()
    pm.write_payload({"source": "test"})
    pm.clear_payload()
    assert pm.read_payload() == []


def test_clear_payload_idempotent():
    pm = PayloadManager()
    pm.clear_payload()
    pm.clear_payload()
    assert pm.read_payload() == []


def test_initial_payload_is_empty():
    pm = PayloadManager()
    assert pm.read_payload() == []
