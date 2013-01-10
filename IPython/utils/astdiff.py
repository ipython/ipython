# encoding: utf-8
"""
Find first change in abstract syntax tree
"""

import os
import shutil
import ast

def get_change_file(filename, tracking_file, change_file):
    """
    Compare two files and create a file starting at the first change found

    Returns name of the original file if no tracking file found (because
    then all content of original file can be considered new and the
    original file can serve as the change file)

    Returns name of change file if differences found

    Returns ``None`` if there no differences found
    """
    if not os.path.exists(tracking_file):
        shutil.copy(filename, tracking_file)
        return filename
    else:
        # store file content because will use later
        file_content = open(filename, 'r').read()
        file_ast = ast.parse(file_content)
        track_ast = ast.parse(open(tracking_file, 'r').read())
        lineno = get_diff_lineno(file_ast, track_ast)
        if lineno is None:
            return None
        # make temporary file to send to run
        changed = [ln for i, ln in enumerate(file_content.splitlines())
                   if i >= lineno]
        with open(change_file, 'w') as chngf:
            chngf.write('\n'.join(changed))
        # update tracking file
        shutil.copy(filename, tracking_file)
        return change_file


def get_diff_lineno(main_ast, ref_ast):
    """
    Get line number of the first difference found between ast bodies

    Second ast is used as a reference.
    """
    # extend tracking to file length if needed
    mbs = [b for b in main_ast.body]
    rbs = [b for b in ref_ast.body]
    lendiff = len(mbs) - len(rbs)
    if lendiff > 0:
        rbs.extend([None] * lendiff)
    # compare file and tracked file trees
    # stop at the first place trees are not equal
    for mb, rb in zip(mbs, rbs):
        if rb is None or not ast.dump(mb) == ast.dump(rb):
            return mb.lineno - 1
    return None
