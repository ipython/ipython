from IPython.core.tips import _tips

import os
import pytest

all_tips = _tips["random"] + list(_tips["every_year"].values())


@pytest.mark.skipif(os.name != "nt", reason="Windows console may crash with Unicode")
@pytest.mark.parametrize("tip", all_tips)
def test_tips(tip):
    assert tip.isascii()
