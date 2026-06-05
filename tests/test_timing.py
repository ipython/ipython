"""Tests for IPython.utils.timing."""

import pytest

from IPython.utils.timing import clock, clock2, timing, timings, timings_out


def test_clock_returns_float():
    t = clock()
    assert isinstance(t, float)
    assert t >= 0.0


def test_clock2_returns_two_floats():
    u, s = clock2()
    assert isinstance(u, float)
    assert isinstance(s, float)
    assert u >= 0.0
    assert s >= 0.0


def test_timings_out_reps_1():
    total, per_call, result = timings_out(1, lambda: 42)
    assert result == 42
    assert isinstance(total, float)
    assert isinstance(per_call, float)
    assert total >= 0.0
    assert per_call >= 0.0


def test_timings_out_reps_multiple():
    counter = [0]

    def increment():
        counter[0] += 1

    timings_out(5, increment)
    assert counter[0] == 5


def test_timings_out_returns_last_output():
    results = []

    def make_result():
        results.append(len(results))
        return len(results)

    _, _, out = timings_out(3, make_result)
    assert out == 3


def test_timings_out_invalid_reps_raises():
    with pytest.raises(ValueError, match="reps must be >= 1"):
        timings_out(0, lambda: None)


def test_timings_out_negative_reps_raises():
    with pytest.raises(ValueError):
        timings_out(-1, lambda: None)


def test_timings_returns_two_floats():
    total, per_call = timings(3, lambda: None)
    assert isinstance(total, float)
    assert isinstance(per_call, float)
    assert total >= 0.0


def test_timing_returns_float():
    t = timing(lambda: None)
    assert isinstance(t, float)
    assert t >= 0.0


@pytest.mark.parametrize("reps", [1, 2, 5, 10])
def test_timings_per_call_equals_total_divided_by_reps(reps):
    total, per_call = timings(reps, lambda: None)
    assert abs(per_call - total / reps) < 1e-10


def test_timings_out_passes_args_and_kwargs():
    def add(a, b, c=0):
        return a + b + c

    _, _, result = timings_out(1, add, 1, 2, c=3)
    assert result == 6
