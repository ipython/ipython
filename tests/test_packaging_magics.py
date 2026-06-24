from unittest import mock

import pytest

from IPython.core.magics.packaging import PackagingMagics


class Shell:
    kernel = None

    def __init__(self):
        self.commands = []

    def system(self, command):
        self.commands.append(command)


@pytest.mark.parametrize(
    ("platform", "executable", "prefix", "expected"),
    [
        (
            "linux",
            "/tmp/conda root/bin/conda",
            "/tmp/env with spaces",
            "'/tmp/conda root/bin/conda' install --prefix "
            "'/tmp/env with spaces' --file 'spec file.txt'",
        ),
        (
            "win32",
            r"C:\conda root\conda.exe",
            r"C:\env with spaces",
            r'"C:\conda root\conda.exe" install --prefix '
            r'"C:\env with spaces" --file "spec file.txt"',
        ),
    ],
)
def test_conda_command_quotes_paths_with_spaces(platform, executable, prefix, expected):
    shell = Shell()
    magics = PackagingMagics(shell)

    with (
        mock.patch("IPython.core.magics.packaging.sys.platform", platform),
        mock.patch("IPython.core.magics.packaging.sys.prefix", prefix),
    ):
        magics._run_command(executable, 'install --file "spec file.txt"')

    assert shell.commands == [expected]
