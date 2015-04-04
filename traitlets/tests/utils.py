import sys
import nose.tools as nt

from subprocess import Popen, PIPE

def get_output_error_code(cmd):
    """Get stdout, stderr, and exit code from running a command"""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    out = out.decode('utf8', 'replace')
    err = err.decode('utf8', 'replace')
    return out, err, p.returncode


def check_help_output(pkg, subcommand=None):
    """test that `python -m PKG [subcommand] -h` works"""
    cmd = [sys.executable, '-m', pkg]
    if subcommand:
        cmd.extend(subcommand)
    cmd.append('-h')
    out, err, rc = get_output_error_code(cmd)
    nt.assert_equal(rc, 0, err)
    nt.assert_not_in("Traceback", err)
    nt.assert_in("Options", out)
    nt.assert_in("--help-all", out)
    return out, err


def check_help_all_output(pkg, subcommand=None):
    """test that `python -m PKG --help-all` works"""
    cmd = [sys.executable, '-m', pkg]
    if subcommand:
        cmd.extend(subcommand)
    cmd.append('--help-all')
    out, err, rc = get_output_error_code(cmd)
    nt.assert_equal(rc, 0, err)
    nt.assert_not_in("Traceback", err)
    nt.assert_in("Options", out)
    nt.assert_in("Class parameters", out)
    return out, err
