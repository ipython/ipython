"""
Test for async helpers. 

Should only trigger on python 3.5+ or will have syntax errors.
"""

import sys
import nose.tools as nt
from textwrap import dedent
from unittest import TestCase

ip = get_ipython()
iprc = lambda x: ip.run_cell(dedent(x))

if sys.version_info > (3,5):
    from IPython.core.async_helpers import _should_be_async

    class AsyncTest(TestCase):

        def test_should_be_async(self):
            nt.assert_false(_should_be_async("False"))
            nt.assert_true(_should_be_async("await bar()"))
            nt.assert_true(_should_be_async("x = await bar()"))
            nt.assert_false(_should_be_async(dedent("""
                async def awaitable():
                    pass
            """)))

        def test_execute(self):
            iprc("""
            import asyncio
            await asyncio.sleep(0.001)
            """)

        def test_autoawait(self):
            ip.run_cell('%autoawait False')
            ip.run_cell('%autoawait True')
            iprc('''
                from asyncio import sleep
                await.sleep(0.1)
            ''')

        def test_autoawait_curio(self):
            ip.run_cell('%autoawait curio')

        def test_autoawait_trio(self):
            ip.run_cell('%autoawait trio')

        def tearDown(self):
            ip.loop_runner = 'asyncio'


