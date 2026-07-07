# coding: utf-8
"""Tests for IPython.core.historyapp"""

import sqlite3
import sys
from contextlib import closing

import pytest

from traitlets.config.configurable import SingletonConfigurable

from IPython.core.historyapp import HistoryApp, HistoryClear, HistoryTrim


def _clear_singleton(inst):
    """Unregister a SingletonConfigurable instance created via a subcommand."""
    for klass in type(inst).__mro__:
        if klass is SingletonConfigurable:
            break
        if getattr(klass, "_instance", None) is inst:
            klass._instance = None


def _make_history_db(hist_file, n_inputs):
    """Create a history database with ``n_inputs`` input lines in one session."""
    with closing(sqlite3.connect(hist_file)) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS sessions (session integer
            primary key autoincrement, start timestamp,
            end timestamp, num_cmds integer, remark text)"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS history
            (session integer, line integer, source text, source_raw text,
            PRIMARY KEY (session, line))"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS output_history
            (session integer, line integer, output text,
            PRIMARY KEY (session, line))"""
        )
        db.execute(
            "INSERT INTO sessions VALUES (1, '2020-01-01 00:00:00', "
            "'2020-01-01 01:00:00', ?, 'test session')",
            (n_inputs,),
        )
        for i in range(1, n_inputs + 1):
            db.execute(
                "INSERT INTO history VALUES (1, ?, ?, ?)",
                (i, "x = %d" % i, "x = %d" % i),
            )
        db.execute("INSERT INTO output_history VALUES (1, 1, '1')")
        db.commit()


def _input_sources(hist_file):
    with closing(sqlite3.connect(hist_file)) as db:
        return [
            row[0]
            for row in db.execute("SELECT source FROM history ORDER BY session, line")
        ]


@pytest.fixture
def ipython_dir(tmp_path, monkeypatch):
    """A temporary IPYTHONDIR with a default profile holding 10 history entries."""
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path))
    # initialize() installs a crash handler; restore sys.excepthook afterwards
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    profile_dir = tmp_path / "profile_default"
    profile_dir.mkdir()
    _make_history_db(profile_dir / "history.sqlite", 10)
    return tmp_path


def test_history_trim(ipython_dir, capsys):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    app = HistoryTrim()
    app.initialize(["--keep=5"])
    app.start()
    out = capsys.readouterr().out
    assert "Trimming history to the most recent 5 entries." in out
    assert _input_sources(hist_file) == ["x = %d" % i for i in range(6, 11)]


def test_history_trim_noop(ipython_dir, capsys):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    app = HistoryTrim()
    app.initialize(["--keep=100"])
    app.start()
    out = capsys.readouterr().out
    assert "There are already at most 100 entries" in out
    assert len(_input_sources(hist_file)) == 10


def test_history_trim_backup(ipython_dir, capsys):
    profile_dir = ipython_dir / "profile_default"
    # an existing backup must not be overwritten
    existing_backup = profile_dir / "history.sqlite.old.1"
    existing_backup.write_text("previous backup", encoding="utf-8")
    app = HistoryTrim()
    app.initialize(["--backup", "--keep=3"])
    app.start()
    out = capsys.readouterr().out
    assert "Backed up longer history file to" in out
    assert existing_backup.read_text(encoding="utf-8") == "previous backup"
    backup = profile_dir / "history.sqlite.old.2"
    assert backup.exists()
    assert len(_input_sources(backup)) == 10
    assert len(_input_sources(profile_dir / "history.sqlite")) == 3


def test_history_trim_dodges_existing_new_file(ipython_dir):
    # a leftover history.sqlite.new must not be clobbered
    profile_dir = ipython_dir / "profile_default"
    leftover = profile_dir / "history.sqlite.new"
    leftover.write_text("do not touch", encoding="utf-8")
    app = HistoryTrim()
    app.initialize(["--keep=2"])
    app.start()
    assert leftover.read_text(encoding="utf-8") == "do not touch"
    assert len(_input_sources(profile_dir / "history.sqlite")) == 2


def test_history_clear_force(ipython_dir, capsys):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    app = HistoryClear()
    app.initialize(["--force"])
    app.start()
    assert _input_sources(hist_file) == []


def test_history_clear_answer_no(ipython_dir, monkeypatch):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    monkeypatch.setattr(
        "IPython.core.historyapp.ask_yes_no", lambda *args, **kwargs: False
    )
    app = HistoryClear()
    app.initialize([])
    app.start()
    # user said no: history left alone
    assert len(_input_sources(hist_file)) == 10


def test_history_clear_answer_yes(ipython_dir, monkeypatch):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    monkeypatch.setattr(
        "IPython.core.historyapp.ask_yes_no", lambda *args, **kwargs: True
    )
    app = HistoryClear()
    app.initialize([])
    app.start()
    assert _input_sources(hist_file) == []


def test_history_app_no_subcommand(capsys):
    app = HistoryApp()
    app.initialize([])
    with pytest.raises(SystemExit):
        app.start()
    out = capsys.readouterr().out
    assert "No subcommand specified" in out
    assert "trim" in out
    assert "clear" in out


def test_history_app_trim_subcommand(ipython_dir, capsys):
    hist_file = ipython_dir / "profile_default" / "history.sqlite"
    app = HistoryApp()
    app.initialize(["trim", "--keep=4"])
    try:
        app.start()
    finally:
        _clear_singleton(app.subapp)
    out = capsys.readouterr().out
    assert "Trimming history to the most recent 4 entries." in out
    assert len(_input_sources(hist_file)) == 4
