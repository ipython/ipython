from pathlib import Path

from IPython.utils.openpy import detect_encoding, read_py_file, source_to_unicode

nonascii_path = Path(__file__).parent / "../../core/tests/nonascii.py"


def test_detect_encoding():
    with nonascii_path.open("rb") as f:
        enc, lines = detect_encoding(f.readline)
    assert enc == "iso-8859-5"


def test_read_file():
    with nonascii_path.open(encoding="iso-8859-5") as f:
        read_specified_enc = f.read()
    read_detected_enc = read_py_file(nonascii_path, skip_encoding_cookie=False)
    assert read_detected_enc == read_specified_enc
    assert "coding: iso-8859-5" in read_detected_enc

    read_strip_enc_cookie = read_py_file(nonascii_path, skip_encoding_cookie=True)
    assert "coding: iso-8859-5" not in read_strip_enc_cookie


def test_source_to_unicode():
    with nonascii_path.open("rb") as f:
        source_bytes = f.read()
    assert (
        source_to_unicode(source_bytes, skip_encoding_cookie=False).splitlines()
        == source_bytes.decode("iso-8859-5").splitlines()
    )

    source_no_cookie = source_to_unicode(source_bytes, skip_encoding_cookie=True)
    assert "coding: iso-8859-5" not in source_no_cookie
