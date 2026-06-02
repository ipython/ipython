"""Unit tests for IPython.core.logger.Logger"""

import os

import pytest

from IPython.core.logger import Logger


@pytest.fixture
def logger(tmp_path):
    return Logger(home_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# logmode property
# ---------------------------------------------------------------------------


def test_default_logmode(logger):
    assert logger.logmode == "over"


@pytest.mark.parametrize("mode", ["append", "backup", "global", "over", "rotate"])
def test_valid_logmode(logger, mode):
    logger.logmode = mode
    assert logger.logmode == mode


def test_invalid_logmode_raises(logger):
    with pytest.raises(ValueError, match="invalid log mode"):
        logger.logmode = "bogus"


# ---------------------------------------------------------------------------
# initial state
# ---------------------------------------------------------------------------


def test_initial_log_active_is_false(logger):
    assert logger.log_active is False


def test_initial_logfile_is_none(logger):
    assert logger.logfile is None


def test_initial_log_raw_input_is_false(logger):
    assert logger.log_raw_input is False


def test_initial_log_output_is_false(logger):
    assert logger.log_output is False


def test_initial_timestamp_is_false(logger):
    assert logger.timestamp is False


# ---------------------------------------------------------------------------
# logstart / logstop
# ---------------------------------------------------------------------------


def test_logstart_over_mode(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    assert logger.log_active is True
    assert logger.logfile is not None
    logger.logstop()


def test_logstart_raises_if_already_active(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    try:
        with pytest.raises(RuntimeError, match="already active"):
            logger.logstart(logfname=logfname)
    finally:
        logger.logstop()


def test_logstop_closes_file(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    logger.logstop()
    assert logger.logfile is None
    assert logger.log_active is False


def test_logstop_when_not_started_does_not_raise(logger, capsys):
    logger.logstop()
    out = capsys.readouterr().out
    assert "hadn't been started" in out


def test_logstart_append_mode(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="append")
    logger.log_write("line1\n")
    logger.logstop()
    logger.logstart(logfname=logfname, logmode="append")
    logger.log_write("line2\n")
    logger.logstop()
    content = (tmp_path / "test.log").read_text()
    assert "line1" in content
    assert "line2" in content


# ---------------------------------------------------------------------------
# log_write
# ---------------------------------------------------------------------------


def test_log_write_when_inactive_does_nothing(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    logger.logstop()
    logger.log_write("should not appear\n")
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "should not appear" not in content


def test_log_write_input(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    logger.log_write("hello = 1\n")
    logger.logstop()
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "hello = 1" in content


def test_log_write_output(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over", log_output=True)
    logger.log_write("result\n", kind="output")
    logger.logstop()
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "#[Out]#" in content
    assert "result" in content


def test_log_write_output_suppressed_when_flag_off(logger, tmp_path):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over", log_output=False)
    logger.log_write("result\n", kind="output")
    logger.logstop()
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "#[Out]#" not in content


# ---------------------------------------------------------------------------
# switch_log
# ---------------------------------------------------------------------------


def test_switch_log_toggles_active(logger, tmp_path, capsys):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    assert logger.log_active is True
    logger.switch_log(False)
    assert logger.log_active is False
    logger.switch_log(True)
    assert logger.log_active is True
    logger.logstop()


def test_switch_log_when_no_file_prints_message(logger, capsys):
    logger.switch_log(True)
    out = capsys.readouterr().out
    assert "logstart" in out


# ---------------------------------------------------------------------------
# logstate
# ---------------------------------------------------------------------------


def test_logstate_when_inactive(logger, capsys):
    logger.logstate()
    out = capsys.readouterr().out
    assert "not been activated" in out


def test_logstate_when_active(logger, tmp_path, capsys):
    logfname = str(tmp_path / "test.log")
    logger.logstart(logfname=logfname, logmode="over")
    logger.logstate()
    logger.logstop()
    out = capsys.readouterr().out
    assert "active" in out
    assert logfname in out
