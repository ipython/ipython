"""
Test for async helpers. 

Should only trigger on python 3.5+ or will have syntax errors.
"""

import sys
import nose.tools as nt
from textwrap import dedent

iprs = lambda x :get_ipython().run_cell(dedent(x))

if sys.version_info > (3,6):
    from IPython.core.async_helpers import _should_be_async

    def test_should_be_async():
        nt.assert_false(_should_be_async("False"))
        nt.assert_true(_should_be_async("await bar()"))
        nt.assert_true(_should_be_async("x = await bar()"))
        nt.assert_false(_should_be_async(dedent("""
            async def awaitable():
                pass
        """)))

    def test_execute():
        iprs("""
        import asyncio
        await asyncio.sleep(0.001)
        """)
