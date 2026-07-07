"""Tests for pylab tools module."""

# -----------------------------------------------------------------------------
# Copyright (c) 2011, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Stdlib imports
import threading
import time

# Third-party imports
import pytest

# Our own imports
from IPython.lib import backgroundjobs as bg

# -----------------------------------------------------------------------------
# Globals and constants
# -----------------------------------------------------------------------------
t_short = 0.0001  # very short interval to wait on jobs


# -----------------------------------------------------------------------------
# Local utilities
# -----------------------------------------------------------------------------
def sleeper(interval=t_short, *a, **kw):
    args = dict(interval=interval, other_args=a, kw_args=kw)
    time.sleep(interval)
    return args


def crasher(interval=t_short, *a, **kw):
    time.sleep(interval)
    raise Exception("Dead job with interval %s" % interval)


# -----------------------------------------------------------------------------
# Classes and functions
# -----------------------------------------------------------------------------


def test_result():
    """Test job submission and result retrieval"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new(sleeper)
    j.join()
    assert j.result["interval"] == t_short


def test_flush():
    """Test job control"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new(sleeper)
    j.join()
    assert len(jobs.completed) == 1
    assert len(jobs.dead) == 0
    jobs.flush()
    assert len(jobs.completed) == 0


def test_dead():
    """Test control of dead jobs"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new(crasher)
    j.join()
    assert len(jobs.completed) == 0
    assert len(jobs.dead) == 1
    jobs.flush()
    assert len(jobs.dead) == 0


def test_longer():
    """Test control of longer-running jobs"""
    jobs = bg.BackgroundJobManager()
    # Sleep for long enough for the following two checks to still report the
    # job as running, but not so long that it makes the test suite noticeably
    # slower.
    j = jobs.new(sleeper, 0.1)
    assert len(jobs.running) == 1
    assert len(jobs.completed) == 0
    j.join()
    assert len(jobs.running) == 0
    assert len(jobs.completed) == 1


def test_expression_job():
    """Jobs can be created from strings evaluated with given namespaces"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new("x + y", dict(x=1, y=2))
    j.join()
    assert j.result == 3
    # separate globals and locals
    j = jobs.new("x + y", dict(x=10), dict(y=20))
    j.join()
    assert j.result == 30


def test_expression_job_caller_namespace():
    """With no namespace args, the caller's frame is used"""
    jobs = bg.BackgroundJobManager()
    only_visible_here = 21
    j = jobs.new("only_visible_here * 2")
    j.join()
    assert j.result == 42


def test_expression_job_too_many_args():
    jobs = bg.BackgroundJobManager()
    with pytest.raises(ValueError):
        jobs.new("1 + 1", {}, {}, {})


def test_new_invalid_type():
    jobs = bg.BackgroundJobManager()
    with pytest.raises(TypeError):
        jobs.new(42)


def test_base_job_not_instantiable():
    with pytest.raises(NotImplementedError):
        bg.BackgroundJobBase()


def test_func_job_requires_callable():
    with pytest.raises(TypeError):
        bg.BackgroundJobFunc("not a callable")


def test_daemon_flag():
    jobs = bg.BackgroundJobManager()
    ev = threading.Event()
    j = jobs.new(ev.wait, 5, daemon=True)
    assert j.daemon
    ev.set()
    j.join(timeout=5)
    assert not j.is_alive()


def test_getitem():
    """Jobs can be looked up by number or by the job object itself"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new(sleeper)
    j.join()
    assert jobs[j.num] is j
    assert jobs[j] is j


def test_str_and_repr():
    jobs = bg.BackgroundJobManager()
    j = jobs.new("1 + 1")
    j.join()
    assert str(j) == "1 + 1"
    assert repr(j) == "<BackgroundJob #%d: 1 + 1>" % j.num


def test_status_call(capsys):
    """Calling the manager prints a status report of all groups"""
    jobs = bg.BackgroundJobManager()
    ev = threading.Event()
    running = jobs.new(ev.wait, 5)
    completed = jobs.new(sleeper)
    dead = jobs.new(crasher)
    completed.join()
    dead.join()
    try:
        jobs()  # alias for jobs.status()
    finally:
        ev.set()
        running.join(timeout=5)
    out = capsys.readouterr().out
    assert "Running jobs:" in out
    assert "Completed jobs:" in out
    assert "Dead jobs:" in out
    assert "%s : %s" % (completed.num, completed) in out


def test_status_new(capsys):
    """_status_new only reports jobs finished since the last call"""
    jobs = bg.BackgroundJobManager()
    j = jobs.new(sleeper)
    j.join()
    assert jobs._status_new() is True
    out = capsys.readouterr().out
    assert "Completed jobs:" in out
    # state was reset: nothing new to report the second time
    assert not jobs._status_new()


def test_remove():
    jobs = bg.BackgroundJobManager()
    ok = jobs.new(sleeper)
    bad = jobs.new(crasher)
    ok.join()
    bad.join()
    jobs.remove(ok.num)
    assert len(jobs.completed) == 0
    jobs.remove(bad.num)
    assert len(jobs.dead) == 0


def test_remove_running_and_missing(caplog):
    jobs = bg.BackgroundJobManager()
    ev = threading.Event()
    j = jobs.new(ev.wait, 5)
    try:
        jobs.remove(j.num)
        assert "still running" in caplog.text
        assert len(jobs.running) == 1
        caplog.clear()
        jobs.remove(1234)
        assert "not found" in caplog.text
    finally:
        ev.set()
        j.join(timeout=5)


def test_flush_empty(capsys):
    jobs = bg.BackgroundJobManager()
    jobs.flush()
    assert "No jobs to flush." in capsys.readouterr().out


def test_result_method(caplog):
    jobs = bg.BackgroundJobManager()
    j = jobs.new("6 * 7")
    j.join()
    assert jobs.result(j.num) == 42
    jobs.result(1234)
    assert "not found" in caplog.text


def test_traceback(capsys, caplog):
    jobs = bg.BackgroundJobManager()
    j = jobs.new(crasher)
    j.join()
    # traceback of a specific job, by number and by job object
    jobs.traceback(j.num)
    out = capsys.readouterr().out
    assert "Dead job with interval" in out
    jobs.traceback(j)
    assert "Dead job with interval" in capsys.readouterr().out
    # with no argument, print tracebacks for all dead jobs
    jobs.traceback()
    out = capsys.readouterr().out
    assert "Traceback for: %r" % j in out
    assert "Dead job with interval" in out
    # missing job number logs an error
    jobs.traceback(1234)
    assert "not found" in caplog.text


def test_dead_job_attributes():
    jobs = bg.BackgroundJobManager()
    j = jobs.new(crasher)
    j.join()
    assert j.stat_code == bg.BackgroundJobBase.stat_dead_c
    assert j.finished is None
    assert "died" in j.result
    assert "Dead job with interval" in j._tb


def test_traceback_without_ipython(monkeypatch):
    """Without an IPython instance, _init falls back to AutoFormattedTB.

    Note: the fallback currently passes the removed ``color_scheme``
    argument to AutoFormattedTB, so job creation raises TypeError.  This
    test documents the current behaviour; if the fallback is fixed, it
    should be updated to assert that the job runs and formats a traceback.
    """
    monkeypatch.setattr(bg, "get_ipython", lambda: None)
    jobs = bg.BackgroundJobManager()
    with pytest.raises(TypeError):
        jobs.new(crasher)
