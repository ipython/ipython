# encoding: utf-8
"""Tests for io.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from io import StringIO

import pytest

from IPython.utils.io import Tee, capture_output


def test_tee_simple():
    "Very simple check with stdout only"
    chan = StringIO()
    text = "Hello"
    tee = Tee(chan, channel="stdout")
    print(text, file=chan)
    assert chan.getvalue() == text + "\n"
    tee.close()


@pytest.mark.parametrize("channel", ["stdout", "stderr"])
def test_tee_channel(channel):
    trap = StringIO()
    chan = StringIO()
    text = "Hello"

    std_ori = getattr(sys, channel)
    setattr(sys, channel, trap)

    tee = Tee(chan, channel=channel)

    print(text, end="", file=chan)
    assert chan.getvalue() == text

    tee.close()

    setattr(sys, channel, std_ori)
    assert getattr(sys, channel) == std_ori


def test_tee_invalid_channel():
    with pytest.raises(ValueError, match="Invalid channel spec"):
        Tee(StringIO(), channel="invalid")


def test_capture_output():
    with capture_output() as io:
        print("hi, stdout")
        print("hi, stderr", file=sys.stderr)

    assert io.stdout == "hi, stdout\n"
    assert io.stderr == "hi, stderr\n"


def test_capture_output_empty():
    with capture_output() as io:
        pass

    assert io.stdout == ""
    assert io.stderr == ""


def test_tee_isatty():
    chan = StringIO()
    tee = Tee(chan, channel="stdout")
    assert tee.isatty() is False
    tee.close()
