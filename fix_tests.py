import re
from pathlib import Path

content = Path('tests/test_history.py').read_text()

# Fix test_history
content = re.sub(
    r'def test_history\(hmmax2\):\n    ip = get_ipython\(\)\n    with TemporaryDirectory\(\) as tmpdir:\n        tmp_path = Path\(tmpdir\)\n        hist_manager_ori = ip.history_manager\n        hist_file = tmp_path / "history_test_history1.sqlite"\n        new_hm = None\n        try:\n            new_hm = HistoryManager\(shell=ip, hist_file=hist_file\)\n            ip.history_manager = new_hm',
    'def test_history(hmmax2):\n    ip = get_ipython()\n    with TemporaryDirectory() as tmpdir:\n        tmp_path = Path(tmpdir)\n        hist_manager_ori = ip.history_manager\n        hist_file = tmp_path / "history_test_history1.sqlite"\n        new_hm = None\n        try:\n            new_hm = HistoryManager(shell=ip, hist_file=hist_file)\n            ip.history_manager = new_hm',
    content
)

# Replace the info check part
content = re.sub(
    r'            assert sessid < hist\[0\]\n            assert hist\[1:\] == \(lineno, entry\)\n        finally:\n            if new_hm is not None:\n                # Ensure saving thread is shut down before we try to clean up the files\n                new_hm.end_session\(\)\n                # Forcibly close database rather than relying on garbage collection\n                if new_hm.save_thread is not None:\n                    new_hm.save_thread.stop\(\)\n                new_hm.db.close\(\)\n            # swap back\n            ip.history_manager = hist_manager_ori\n    info = ip.history_manager.get_session_info\(\)\n    assert isinstance\(info\[1\], datetime\)',
    '            assert sessid < hist[0]\n            assert hist[1:] == (lineno, entry)\n        finally:\n            if new_hm is not None:\n                # Ensure saving thread is shut down before we try to clean up the files\n                new_hm.end_session()\n                # Forcibly close database rather than relying on garbage collection\n                if new_hm.save_thread is not None:\n                    new_hm.save_thread.stop()\n                new_hm.db.close()\n            # swap back\n            ip.history_manager = hist_manager_ori\n\ndef test_history_session_info():\n    ip = get_ipython()\n    info = ip.history_manager.get_session_info()\n    assert isinstance(info[1], datetime)',
    content
)

Path('tests/test_history.py').write_text(content)
