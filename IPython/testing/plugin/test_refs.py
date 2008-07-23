def test_refs():
    """DocTest reference holding issues when running scripts.

    In [32]: run show_refs.py
    c referrers: [<type 'dict'>]

    In [33]: map(type,gc.get_referrers(c))
    Out[33]: [<type 'dict'>]

    """
    pass
