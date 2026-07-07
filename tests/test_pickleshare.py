"""Tests for the vendored pickleshare module."""

import errno
from pathlib import Path

import pytest

from IPython.external.pickleshare import PickleShareDB, PickleShareLink, gethashfile


@pytest.fixture
def db(tmp_path):
    return PickleShareDB(tmp_path / "pickleshare")


def test_init_creates_directory(tmp_path):
    root = tmp_path / "some" / "nested" / "dir"
    assert not root.exists()
    db = PickleShareDB(root)
    assert root.is_dir()
    assert db.root == root


def test_init_accepts_str_and_existing_dir(tmp_path):
    # a string root and an already-existing directory both work
    db = PickleShareDB(str(tmp_path))
    assert db.root == tmp_path
    db2 = PickleShareDB(tmp_path)
    assert db2.root == tmp_path


def test_init_mkdir_race_is_tolerated(tmp_path, monkeypatch):
    # if another process creates the directory between the is_dir check and
    # mkdir, the resulting EEXIST error is swallowed
    root = tmp_path / "race"

    def racing_mkdir(self, *args, **kwargs):
        raise OSError(errno.EEXIST, "created concurrently")

    monkeypatch.setattr(Path, "mkdir", racing_mkdir)
    db = PickleShareDB(root)
    assert db.cache == {}


def test_init_mkdir_other_errors_propagate(tmp_path, monkeypatch):
    root = tmp_path / "denied"

    def failing_mkdir(self, *args, **kwargs):
        raise OSError(errno.EACCES, "permission denied")

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)
    with pytest.raises(OSError):
        PickleShareDB(root)


def test_setitem_getitem_roundtrip(db):
    db["hello"] = 15
    db["aku ankka"] = [1, 2, 313]
    assert db["hello"] == 15
    assert db["aku ankka"] == [1, 2, 313]


def test_nested_keys_create_parent_dirs(db):
    db["paths/are/ok/key"] = [1, (5, 46)]
    assert (db.root / "paths" / "are" / "ok" / "key").is_file()
    assert db["paths/are/ok/key"] == [1, (5, 46)]


def test_getitem_missing_key_raises_keyerror(db):
    with pytest.raises(KeyError):
        db["nonexistent"]


def test_getitem_corrupt_file_raises_keyerror(db):
    (db.root / "corrupt").write_bytes(b"this is not a pickle")
    with pytest.raises(KeyError):
        db["corrupt"]


def test_cache_returns_same_object_when_unmodified(db):
    db["key"] = [1, 2, 3]
    # once an entry is cached with the file's (integer) mtime, repeated
    # reads must hit the cache and return the identical object, not a new
    # unpickled copy each time
    first = db["key"]
    assert db["key"] is first
    assert first == [1, 2, 3]


def test_uncache_specific_and_all(db):
    db["a"] = 1
    db["b"] = 2
    assert len(db.cache) == 2
    db.uncache(db.root / "a")
    assert db.root / "a" not in db.cache
    assert db.root / "b" in db.cache
    # a fresh read repopulates the cache with a new (unpickled) object
    assert db["a"] == 1
    db.uncache()
    assert db.cache == {}
    # uncaching an unknown item is a no-op
    db.uncache("never seen")


def test_delitem(db):
    db["gone"] = "soon"
    del db["gone"]
    assert "gone" not in db
    with pytest.raises(KeyError):
        db["gone"]
    # deleting a missing key must not raise (concurrent deletion is ok)
    del db["gone"]


def test_keys_iter_len(db):
    db["a"] = 1
    db["sub/b"] = 2
    db["sub/c"] = 3
    assert sorted(db.keys()) == ["a", "sub/b", "sub/c"]
    assert sorted(db) == ["a", "sub/b", "sub/c"]
    assert len(db) == 3


def test_keys_glob(db):
    db["a"] = 1
    db["sub/b"] = 2
    db["sub/c"] = 3
    assert sorted(db.keys("sub/*")) == ["sub/b", "sub/c"]
    assert db.keys("nothing/*") == []


def test_gethashfile_is_stable_two_hex_chars():
    hf = gethashfile("some key")
    assert len(hf) == 2
    int(hf, 16)  # must be valid hex
    assert gethashfile("some key") == hf


def test_hset_hget(db):
    db.hset("hashroot", "key1", "value1")
    db.hset("hashroot", "key2", "value2")
    assert db.hget("hashroot", "key1") == "value1"
    assert db.hget("hashroot", "key2") == "value2"


def test_hget_default_and_missing(db):
    db.hset("hashroot", "key1", "value1")
    assert db.hget("hashroot", "missing", "fallback") == "fallback"
    with pytest.raises(KeyError):
        db.hget("hashroot", "missing")
    # missing hashroot entirely
    with pytest.raises(KeyError):
        db.hget("nosuchroot", "missing")


def test_hset_overwrites(db):
    db.hset("hashroot", "key", "old")
    db.hset("hashroot", "key", "new")
    assert db.hget("hashroot", "key") == "new"


def test_hdict(db):
    values = {"key%d" % i: i for i in range(10)}
    for k, v in values.items():
        db.hset("hashroot", k, v)
    assert db.hdict("hashroot") == values
    assert db.hdict("emptyroot") == {}


def test_hdict_deletes_corrupt_files(db, capsys):
    db.hset("hashroot", "key1", "value1")
    corrupt = db.root / "hashroot" / "aa"
    corrupt.write_bytes(b"not a pickle at all")
    d = db.hdict("hashroot")
    assert d == {"key1": "value1"}
    assert "Corrupt" in capsys.readouterr().out
    # the corrupt bucket file was removed
    assert not corrupt.exists()


def test_hcompress(db):
    values = {"key%d" % i: i for i in range(8)}
    for k, v in values.items():
        db.hset("hashroot", k, v)
    assert len(db.keys("hashroot/*")) > 1
    db.hcompress("hashroot")
    # everything is squashed into the single 'xx' bucket
    assert db.keys("hashroot/*") == ["hashroot/xx"]
    assert db.hdict("hashroot") == values
    # fast hget can't see pre-compression items...
    with pytest.raises(KeyError):
        db.hget("hashroot", "key1")
    # ...but the slow path still finds them
    assert db.hget("hashroot", "key1", fast_only=False) == 1
    # compressing again keeps the 'xx' bucket and all data intact
    db.hcompress("hashroot")
    assert db.keys("hashroot/*") == ["hashroot/xx"]
    assert db.hdict("hashroot") == values


def test_hset_after_hcompress(db):
    db.hset("hashroot", "key1", "value1")
    db.hcompress("hashroot")
    db.hset("hashroot", "key2", "value2")
    # hdict must merge the 'xx' bucket with newer buckets
    assert db.hdict("hashroot") == {"key1": "value1", "key2": "value2"}


def test_waitget_existing_key_returns_immediately(db):
    db["ready"] = 42
    assert db.waitget("ready") == 42


def test_waitget_picks_up_value_after_polling(db, monkeypatch):
    # Deterministically simulate another process writing the key while
    # waitget is polling: the (patched) sleep performs the write.
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        db["later"] = "arrived"

    monkeypatch.setattr("IPython.external.pickleshare.time.sleep", fake_sleep)
    assert db.waitget("later", maxwaittime=10) == "arrived"
    assert sleeps == [0.2]


def test_waitget_times_out(db, monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        "IPython.external.pickleshare.time.sleep", sleeps.append
    )
    with pytest.raises(KeyError):
        db.waitget("never", maxwaittime=1)
    # polling schedule was followed until the accumulated wait passed 1s
    assert sleeps == [0.2, 0.2, 0.2, 0.5]


def test_repr(db):
    assert repr(db) == "PickleShareDB('%s')" % db.root


def test_getlink(db):
    lnk = db.getlink("myobjects/test")
    assert isinstance(lnk, PickleShareLink)
    lnk.foo = 2
    lnk.bar = lnk.foo + 5
    assert lnk.foo == 2
    assert lnk.bar == 7
    # values are stored in the underlying db under the link's key dir
    assert db["myobjects/test/foo"] == 2
    assert db["myobjects/test/bar"] == 7


def test_setitem_tolerates_file_vanishing(db, monkeypatch):
    # if the file is deleted (by another process) between the write and the
    # stat call used to populate the cache, the ENOENT error is swallowed
    real_stat = Path.stat

    def selective_stat(self, *args, **kwargs):
        if self.name == "victim":
            raise OSError(errno.ENOENT, "vanished")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", selective_stat)
    db["victim"] = 1
    assert db.root / "victim" not in db.cache
    monkeypatch.undo()
    assert db["victim"] == 1


def test_setitem_other_stat_errors_propagate(db, monkeypatch):
    real_stat = Path.stat

    def selective_stat(self, *args, **kwargs):
        if self.name == "victim":
            raise OSError(errno.EACCES, "permission denied")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", selective_stat)
    with pytest.raises(OSError):
        db["victim"] = 1


def test_link_repr_is_broken(db):
    # PickleShareLink.__repr__ calls Path.basename(), which does not exist
    # on pathlib.Path objects.  This test documents the current behaviour;
    # if __repr__ is fixed it should assert the repr's content instead.
    lnk = db.getlink("myobjects/test")
    lnk.foo = 2
    with pytest.raises(AttributeError):
        repr(lnk)


def test_mutable_mapping_helpers(db):
    # PickleShareDB is a MutableMapping: get/pop/clear come for free
    db["a"] = 1
    assert db.get("a") == 1
    assert db.get("missing", "default") == "default"
    assert db.pop("a") == 1
    db["b"] = 2
    db["c"] = 3
    db.clear()
    assert len(db) == 0
