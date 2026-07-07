# -*- coding: utf-8 -*-
"""Test IPython.core.logger"""

import os.path
import re

import pytest
from tempfile import TemporaryDirectory

from IPython.core.logger import Logger


def test_logstart_inaccessible_file():
    with pytest.raises(IOError):
        _ip.logger.logstart(logfname="/")  # Opening that filename will fail.

    try:
        _ip.run_cell("a=1")  # Check it doesn't try to log this
    finally:
        _ip.logger.log_active = False  # If this fails, don't let later tests fail


def test_logstart_unicode():
    with TemporaryDirectory() as tdir:
        logfname = os.path.join(tdir, "test_unicode.log")
        _ip.run_cell("'abc€'")
        try:
            _ip.run_line_magic("logstart", "-to %s" % logfname)
            _ip.run_cell("'abc€'")
        finally:
            _ip.logger.logstop()


def test_invalid_logmode_raises(tmp_path):
    with pytest.raises(ValueError, match="invalid log mode"):
        Logger(str(tmp_path), logmode="bogus")
    logger = Logger(str(tmp_path))
    with pytest.raises(ValueError, match="invalid log mode"):
        logger.logmode = "not-a-mode"


def test_logstart_twice_raises(tmp_path):
    logger = Logger(str(tmp_path), logfname=str(tmp_path / "log.py"))
    try:
        logger.logstart()
        with pytest.raises(RuntimeError, match="already active"):
            logger.logstart()
    finally:
        logger.logstop()


def test_logstart_over_mode_truncates(tmp_path):
    logfname = tmp_path / "log.py"
    logfname.write_text("old content\n", encoding="utf-8")
    logger = Logger(str(tmp_path), logfname=str(logfname), loghead="# head\n")
    try:
        logger.logstart()
        logger.log_write("a = 1\n")
    finally:
        logger.logstop()
    assert logfname.read_text(encoding="utf-8") == "# head\na = 1\n"


def test_logstart_append_mode(tmp_path):
    logfname = tmp_path / "log.py"
    logfname.write_text("old content\n", encoding="utf-8")
    logger = Logger(
        str(tmp_path), logfname=str(logfname), loghead="# head\n", logmode="append"
    )
    try:
        logger.logstart()
        logger.log_write("a = 1\n")
    finally:
        logger.logstop()
    # append mode keeps previous content and does not write the log head
    assert logfname.read_text(encoding="utf-8") == "old content\na = 1\n"


def test_logstart_backup_mode(tmp_path):
    logfname = tmp_path / "log.py"
    logfname.write_text("current\n", encoding="utf-8")
    # a stale backup must be replaced, not appended to
    backup = tmp_path / "log.py~"
    backup.write_text("stale backup\n", encoding="utf-8")
    logger = Logger(str(tmp_path), logfname=str(logfname), logmode="backup")
    try:
        logger.logstart()
        logger.log_write("new\n")
    finally:
        logger.logstop()
    assert backup.read_text(encoding="utf-8") == "current\n"
    assert logfname.read_text(encoding="utf-8") == "new\n"


def test_logstart_global_mode(tmp_path):
    logger = Logger(str(tmp_path), logfname="global.py", logmode="global")
    try:
        logger.logstart()
        logger.log_write("x = 1\n")
    finally:
        logger.logstop()
    assert logger.logfname == str(tmp_path / "global.py")
    assert (tmp_path / "global.py").read_text(encoding="utf-8") == "x = 1\n"


def test_logstart_rotate_mode(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname), logmode="rotate")
    for content in ("first\n", "second\n", "third\n"):
        try:
            logger.logstart()
            logger.log_write(content)
        finally:
            logger.logstop()
    assert logfname.read_text(encoding="utf-8") == "third\n"
    assert (tmp_path / "log.py.001~").read_text(encoding="utf-8") == "second\n"
    assert (tmp_path / "log.py.002~").read_text(encoding="utf-8") == "first\n"


def test_log_write_timestamp(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart(timestamp=True)
        logger.log_write("a = 1\n")
    finally:
        logger.logstop()
    lines = logfname.read_text(encoding="utf-8").splitlines()
    assert re.match(r"# \w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2}", lines[0])
    assert lines[1] == "a = 1"


def test_log_write_output(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart(log_output=True)
        logger.log_write("1 + 1\n")
        logger.log_write("2\nmore", kind="output")
    finally:
        logger.logstop()
    assert logfname.read_text(encoding="utf-8") == (
        "1 + 1\n#[Out]# 2\n#[Out]# more\n"
    )


def test_log_write_output_disabled(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart()
        logger.log_write("2", kind="output")
    finally:
        logger.logstop()
    assert logfname.read_text(encoding="utf-8") == ""


def test_log_write_inactive(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart()
        logger.log_active = False
        logger.log_write("should not appear\n")
    finally:
        logger.logstop()
    assert logfname.read_text(encoding="utf-8") == ""


def test_log_raw_input(tmp_path):
    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart(log_raw_input=True)
        logger.log("modified\n", "original\n")
    finally:
        logger.logstop()
    assert logfname.read_text(encoding="utf-8") == "original\n"

    logfname2 = tmp_path / "log2.py"
    logger = Logger(str(tmp_path), logfname=str(logfname2))
    try:
        logger.logstart()
        logger.log("modified\n", "original\n")
    finally:
        logger.logstop()
    assert logfname2.read_text(encoding="utf-8") == "modified\n"


def test_log_write_flush_failure(tmp_path, capsys):
    class FlushFails:
        def __init__(self, f):
            self._f = f

        def write(self, data):
            return self._f.write(data)

        def flush(self):
            raise OSError("disk gone")

        def close(self):
            self._f.close()

    logfname = tmp_path / "log.py"
    logger = Logger(str(tmp_path), logfname=str(logfname))
    try:
        logger.logstart()
        logger.logfile = FlushFails(logger.logfile)
        logger.log_write("a = 1\n")
    finally:
        logger.logstop()
    out = capsys.readouterr().out
    assert "Failed to flush the log file." in out
    assert str(logfname) in out


def test_switch_log_invalid_value(tmp_path):
    logger = Logger(str(tmp_path))
    with pytest.raises(ValueError, match="boolean argument"):
        logger.switch_log("yes")


def test_switch_log_not_started(tmp_path, capsys):
    logger = Logger(str(tmp_path))
    logger.switch_log(True)
    assert "Logging hasn't been started yet" in capsys.readouterr().out


def test_switch_log_toggle(tmp_path, capsys):
    logger = Logger(str(tmp_path), logfname=str(tmp_path / "log.py"))
    try:
        logger.logstart()
        capsys.readouterr()
        logger.switch_log(True)
        assert "Logging is already ON" in capsys.readouterr().out
        logger.switch_log(False)
        assert "Switching logging OFF" in capsys.readouterr().out
        assert logger.log_active is False
        logger.switch_log(True)
        assert "Switching logging ON" in capsys.readouterr().out
        assert logger.log_active is True
    finally:
        logger.logstop()


def test_logstate(tmp_path, capsys):
    logger = Logger(str(tmp_path), logfname=str(tmp_path / "log.py"))
    logger.logstate()
    assert "Logging has not been activated." in capsys.readouterr().out
    try:
        logger.logstart(timestamp=True, log_output=True)
        logger.logstate()
        out = capsys.readouterr().out
        assert "Filename       : %s" % logger.logfname in out
        assert "Mode           : over" in out
        assert "Output logging : True" in out
        assert "Raw input log  : False" in out
        assert "Timestamping   : True" in out
        assert "State          : active" in out
        logger.log_active = False
        logger.logstate()
        assert "temporarily suspended" in capsys.readouterr().out
    finally:
        logger.logstop()


def test_logstop_not_started(tmp_path, capsys):
    logger = Logger(str(tmp_path))
    logger.logstop()
    assert "Logging hadn't been started." in capsys.readouterr().out
    assert logger.log_active is False


def test_close_log_alias(tmp_path):
    logger = Logger(str(tmp_path), logfname=str(tmp_path / "log.py"))
    logger.logstart()
    logger.close_log()
    assert logger.logfile is None
    assert logger.log_active is False
