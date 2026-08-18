"""Check the hand-maintained table of built-in magics against the code.

IPython declares its own magics to ``MagicsManager.lazy_magics`` from the
static table in :mod:`IPython.core.magics._table`, which is only correct as
long as somebody keeps it correct -- that is what this module is for.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import inspect
import pkgutil
import subprocess
import sys
import textwrap
from importlib import import_module

import pytest
from traitlets.config import Config, Configurable

import IPython.core.magics
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShellABC
from IPython.core.magic import LazyMagic, Magics, MagicsManager
from IPython.core.magics import _table

EXECUTION_SPEC = "IPython.core.magics.execution:ExecutionMagics"


def _shipped_magics_classes():
    """Every ``Magics`` subclass defined under ``IPython/core/magics``."""
    found = {}
    for info in pkgutil.iter_modules(IPython.core.magics.__path__):
        module_name = f"{IPython.core.magics.__name__}.{info.name}"
        module = import_module(module_name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, Magics)
                and obj is not Magics
                # Only where it is defined, not where it is imported.
                and obj.__module__ == module_name
            ):
                found[name] = obj
    return found


class _UnconfiguredShell(Configurable):
    """Just enough of a shell for a ``Magics`` class to be instantiated.

    With the *default* configuration, not whatever the session-wide test shell
    has picked up along the way (``test_magic.py`` adds script magics to it).
    """

    def __init__(self):
        super().__init__(config=Config())
        self.configurables = []


# So that `MagicsManager.shell` accepts one of these.
InteractiveShellABC.register(_UnconfiguredShell)


def _expected_table():
    """The table `_table.BUILTIN_LAZY_MAGICS` should hold, plus any name found
    on more than one class, which a flat name -> class mapping cannot express.
    """
    expected = {"line": {}, "cell": {}}
    duplicated = {}
    # ScriptMagics generates one cell magic per configured interpreter; the
    # table only carries the fixed ones, `init_magics` adds the rest.
    generated = set(_table.default_script_magics())
    for class_name, cls in sorted(_shipped_magics_classes().items()):
        spec = f"{cls.__module__}:{class_name}"
        instance = cls(shell=_UnconfiguredShell())
        for kind in ("line", "cell"):
            for name in sorted(instance.magics[kind]):
                if name in generated and class_name == "ScriptMagics":
                    continue
                if name in expected[kind]:
                    duplicated[name] = (expected[kind][name], spec)
                expected[kind][name] = spec
    return expected, duplicated


def _render(table):
    """Render a name table as the source that should live in ``_table.py``."""
    lines = ["BUILTIN_LAZY_MAGICS = {"]
    for kind, names in table.items():
        lines.append(f'    "{kind}": {{')
        for name, spec in sorted(names.items()):
            lines.append(f'        "{name}": "{spec}",')
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


def test_builtin_lazy_magics_table_is_accurate():
    """``BUILTIN_LAZY_MAGICS`` maps every built-in magic to its class."""
    expected, _ = _expected_table()
    declared = {
        kind: dict(sorted(names.items()))
        for kind, names in _table.BUILTIN_LAZY_MAGICS.items()
    }
    assert declared == {k: dict(sorted(v.items())) for k, v in expected.items()}, (
        "IPython.core.magics._table.BUILTIN_LAZY_MAGICS is out of sync with the "
        "magics classes. It should read:\n\n" + _render(expected)
    )


def test_no_magic_is_claimed_by_two_classes():
    """Eagerly, a duplicate resolved to whichever class registered last;
    declared lazily there is one entry per name, so one would be lost.
    """
    _, duplicated = _expected_table()
    assert not duplicated


def test_every_shipped_class_is_in_the_table():
    """A new Magics class must be added to ``BUILTIN_LAZY_MAGICS``."""
    declared = {
        spec.rpartition(":")[2]
        for names in _table.BUILTIN_LAZY_MAGICS.values()
        for spec in names.values()
    }
    missing = set(_shipped_magics_classes()) - declared
    assert not missing, (
        f"{sorted(missing)} are not listed in IPython.core.magics._table."
        "BUILTIN_LAZY_MAGICS, so their magics would not be known at startup."
    )


def test_every_shipped_class_is_importable_from_the_package():
    """``MAGICS_CLASSES`` drives ``IPython.core.magics.__getattr__``."""
    for class_name, cls in _shipped_magics_classes().items():
        assert _table.MAGICS_CLASSES.get(class_name) == cls.__module__, (
            f"IPython.core.magics._table.MAGICS_CLASSES[{class_name!r}] should"
            f" be {cls.__module__!r}"
        )
        assert getattr(IPython.core.magics, class_name) is cls


def test_magics_classes_entries_resolve():
    """Every entry of ``MAGICS_CLASSES`` points at something that exists."""
    for name, module_name in _table.MAGICS_CLASSES.items():
        module = import_module(module_name)
        assert hasattr(module, name), f"{module_name} does not define {name}"
        assert getattr(IPython.core.magics, name) is getattr(module, name)
    assert set(_table.MAGICS_CLASSES) <= set(dir(IPython.core.magics))


def test_registered_names_match_the_table():
    """A live shell knows every magic the table declares."""
    ip = get_ipython()
    for kind in ("line", "cell"):
        declared = set(_table.BUILTIN_LAZY_MAGICS[kind])
        if kind == "cell":
            declared |= set(_table.default_script_magics())
        assert not declared - set(ip.magics_manager.magics[kind])


def test_configured_script_magics():
    assert _table.configured_script_magics(None) == _table.default_script_magics()
    assert _table.configured_script_magics(Config()) == _table.default_script_magics()

    config = Config()
    config.ScriptMagics.script_magics = ["nodejs"]
    assert _table.configured_script_magics(config) == ["nodejs"]


@pytest.fixture
def manager():
    """A standalone MagicsManager, so tests don't disturb the shared shell."""
    return MagicsManager(shell=_UnconfiguredShell())


def test_register_lazy_declares_without_importing(manager):
    manager.register_lazy("timeit", EXECUTION_SPEC, "line_cell")
    assert isinstance(manager.magics["line"]["timeit"], LazyMagic)
    assert isinstance(manager.magics["cell"]["timeit"], LazyMagic)
    assert manager.lazy_magics["timeit"] == EXECUTION_SPEC

    fn = manager.find("line", "timeit")
    assert callable(fn) and not isinstance(fn, LazyMagic)
    assert manager.magics["line"]["timeit"] is fn
    # Loading it registered the whole class, including its cell magics.
    assert not isinstance(manager.magics["cell"]["timeit"], LazyMagic)
    assert manager.registry["ExecutionMagics"].__class__.__name__ == "ExecutionMagics"


def test_placeholder_resolves_on_attribute_access(manager):
    """pyflyby reaches the Magics instance through `magics["line"][name]`."""
    manager.register_lazy("prun", EXECUTION_SPEC, "line")
    placeholder = manager.magics["line"]["prun"]
    assert placeholder.__self__ is manager.registry["ExecutionMagics"]


def test_register_lazy_validates_the_kind(manager):
    with pytest.raises(ValueError):
        manager.register_lazy("timeit", EXECUTION_SPEC, "both")


def test_find_drops_a_placeholder_the_class_does_not_deliver(manager):
    manager.register_lazy("dummy_lazy", EXECUTION_SPEC, "line")
    # ExecutionMagics provides no `%dummy_lazy`, so the declaration was wrong.
    assert manager.find("line", "dummy_lazy") is None
    assert "dummy_lazy" not in manager.magics["line"]
    # And asking again does not resurrect it or re-register the class.
    assert manager.find("line", "dummy_lazy") is None


def test_a_class_is_only_loaded_once(manager):
    manager.register_lazy("timeit", EXECUTION_SPEC, "line")
    manager.register_lazy("prun", EXECUTION_SPEC, "line")
    manager.find("line", "timeit")
    first = manager.registry["ExecutionMagics"]
    manager.find("line", "prun")
    manager.load_lazy("prun")
    assert manager.registry["ExecutionMagics"] is first


def test_load_all_lazy_magics_skips_extensions(manager):
    manager.register_lazy("timeit", EXECUTION_SPEC, "line")
    manager.register_lazy("an_extension_magic", "some.extension.module", "line")
    manager.load_all_lazy_magics()
    assert not isinstance(manager.magics["line"]["timeit"], LazyMagic)
    # Untouched: loading an extension runs arbitrary code, so it waits for the
    # magic to actually be used.
    assert isinstance(manager.magics["line"]["an_extension_magic"], LazyMagic)


def test_load_lazy_trusts_the_placeholder_over_the_trait(manager):
    """`lazy_magics` is user-configurable and may be replaced wholesale."""
    manager.register_lazy("timeit", EXECUTION_SPEC, "line")
    manager.lazy_magics = {"something": "else"}
    assert callable(manager.find("line", "timeit"))


def test_a_failing_lazy_load_is_retried(manager):
    manager.register_lazy("nope", "no.such.module:NoMagics", "line")
    for _ in range(2):
        # Raising the import error again beats reporting the magic as missing.
        with pytest.raises(ModuleNotFoundError):
            manager.find("line", "nope")


def test_registry_loads_a_declared_class_on_a_miss(manager):
    manager.register_lazy("timeit", EXECUTION_SPEC, "line")
    assert "ExecutionMagics" not in dict(manager.registry)
    assert manager.registry["ExecutionMagics"].__class__.__name__ == "ExecutionMagics"
    with pytest.raises(KeyError):
        manager.registry["NoSuchMagics"]


def test_lsmagic_docs_does_not_document_the_placeholder(manager):
    """%magic must not import an extension just to print a docstring."""
    manager.register_lazy("an_extension_magic", "some.extension.module", "line")
    docs = manager.lsmagic_docs(missing="No documentation")
    assert docs["line"]["an_extension_magic"] == "No documentation"


def test_completing_a_declared_magic_does_not_crash():
    """`%timeit x.<TAB>` reaches into the table for the magic's parser."""
    ip = get_ipython()
    ip.Completer.use_jedi = False
    assert ip.Completer._extract_code("%timeit -n 2 -r 1 foo") == "foo"


STARTUP_CHECK = textwrap.dedent(
    """
    import sys
    from IPython.core.interactiveshell import InteractiveShell

    shell = InteractiveShell.instance()
    loaded = sorted(
        name
        for name in sys.modules
        if name.startswith("IPython.core.magics.")
        and not name.rsplit(".", 1)[1].startswith("_")
    )
    print(",".join(loaded))
    """
)


def test_startup_does_not_import_the_magics_modules():
    """The whole point: starting a shell imports no magics implementation."""
    result = subprocess.run(
        [sys.executable, "-c", STARTUP_CHECK],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", (
        "starting a shell imported magics modules eagerly: " + result.stdout
    )
