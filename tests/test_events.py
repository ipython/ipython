import pytest
from unittest.mock import Mock

from IPython.core import events
import IPython.testing.tools as tt


@events._define_event
def ping_received():
    pass


@events._define_event
def event_with_argument(argument):
    pass


@pytest.fixture
def em():
    return events.EventManager(
        get_ipython(),
        {
            "ping_received": ping_received,
            "event_with_argument": event_with_argument,
        },
    )


def test_register_unregister(em):
    cb = Mock()

    em.register("ping_received", cb)
    em.trigger("ping_received")
    assert cb.call_count == 1

    em.unregister("ping_received", cb)
    em.trigger("ping_received")
    assert cb.call_count == 1


def test_bare_function_missed_unregister(em):
    def cb1():
        ...

    def cb2():
        ...

    em.register("ping_received", cb1)
    with pytest.raises(ValueError):
        em.unregister("ping_received", cb2)
    em.unregister("ping_received", cb1)


def test_cb_error(em):
    cb = Mock(side_effect=ValueError)
    em.register("ping_received", cb)
    with tt.AssertPrints("Error in callback"):
        em.trigger("ping_received")


def test_cb_keyboard_interrupt(em):
    cb = Mock(side_effect=KeyboardInterrupt)
    em.register("ping_received", cb)
    with tt.AssertPrints("Error in callback"):
        em.trigger("ping_received")


def test_unregister_during_callback(em):
    invoked = [False] * 3

    def func1(*_):
        invoked[0] = True
        em.unregister("ping_received", func1)
        em.register("ping_received", func3)

    def func2(*_):
        invoked[1] = True
        em.unregister("ping_received", func2)

    def func3(*_):
        invoked[2] = True

    em.register("ping_received", func1)
    em.register("ping_received", func2)

    em.trigger("ping_received")
    assert [True, True, False] == invoked
    assert [func3] == em.callbacks["ping_received"]
