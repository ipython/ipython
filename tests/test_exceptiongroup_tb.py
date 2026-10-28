import unittest
import re
from IPython.utils.capture import capture_output
import sys
import pytest
from tempfile import TemporaryDirectory
from IPython.testing import tools as tt


@pytest.mark.parametrize("outer_chain", ["none", "from", "another"])
@pytest.mark.parametrize("inner_chain", ["none", "from", "another"])
def test_native_exceptiongroup(outer_chain, inner_chain) -> None:
    filestr = f"""
    import pytest

    def f(): raise ValueError("From f()")
    def g(): raise BaseException("From g()")

    def inner(inner_chain):
        excs = []
        for callback in [f, g]:
            try:
                callback()
            except BaseException as err:
                excs.append(err)
        if excs:
            if inner_chain == "none":
                raise BaseExceptionGroup("Oops", excs)
            try:
                raise SyntaxError()
            except SyntaxError as e:
                if inner_chain == "from":
                    raise BaseExceptionGroup("Oops", excs) from e
                else:
                    raise BaseExceptionGroup("Oops", excs)

    def outer(outer_chain, inner_chain):
        try:
            inner(inner_chain)
        except BaseExceptionGroup as e:
            if outer_chain == "none":
                raise
            if outer_chain == "from":
                raise IndexError() from e
            else:
                raise IndexError


    outer("{outer_chain}", "{inner_chain}")
    """
    with capture_output() as cap:
        ip.run_cell(filestr)

    match_lines = []
    if inner_chain == "another":
        match_lines += [
            "During handling of the above exception, another exception occurred:",
        ]
    elif inner_chain == "from":
        match_lines += [
            "The above exception was the direct cause of the following exception:",
        ]

    match_lines += [
        "  + Exception Group Traceback (most recent call last):",
        "  | BaseExceptionGroup: Oops (2 sub-exceptions)",
        "    | ValueError: From f()",
        "    | BaseException: From g()",
    ]

    if outer_chain == "another":
        match_lines += [
            "During handling of the above exception, another exception occurred:",
            "IndexError",
        ]
    elif outer_chain == "from":
        match_lines += [
            "The above exception was the direct cause of the following exception:",
            "IndexError",
        ]

    error_lines = cap.stderr.split("\n")

    for expected in match_lines:
        for i, actual in enumerate(error_lines):
            if actual == expected:
                error_lines = error_lines[i + 1 :]
                break
        else:
            assert False, f"{expected} not found in cap.stderr"
